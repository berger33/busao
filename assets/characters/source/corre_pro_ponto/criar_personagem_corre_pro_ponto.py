# -*- coding: utf-8 -*-
# Blender > Scripting > Open > Run Script (Alt+P).
# Corre pro Ponto: rig, 15 animacoes, cabelo fisico gravado e exportacao GLB.
"""Rig e ciclos FK para a personagem Runner; Blender 4.x/5.x, sem add-ons.

As coordenadas estao em metros; a frente da personagem e -Y no Blender.
API publica: create_rig(collection), create_animations(armature).
"""

import math
import bpy
from mathutils import Matrix, Quaternion, Vector


def create_rig(collection):
    """Cria somente um esqueleto; nao remove objetos ou dados preexistentes."""
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    data = bpy.data.armatures.new('RunnerSkeleton')
    rig = bpy.data.objects.new('RunnerRig', data)
    collection.objects.link(rig)
    rig.select_set(True)
    bpy.context.view_layer.objects.active = rig
    rig.show_in_front = True
    data.display_type = 'OCTAHEDRAL'
    bpy.ops.object.mode_set(mode='EDIT')
    specifications = [
        ('root', (0, 0, 0), (0, 0, .15), None),
        ('pelvis', (0, 0, .89), (0, 0, 1.00), 'root'),
        ('spine', (0, 0, 1.00), (0, 0, 1.13), 'pelvis'),
        ('chest', (0, 0, 1.13), (0, 0, 1.36), 'spine'),
        ('neck', (0, 0, 1.36), (0, 0, 1.46), 'chest'),
        ('head', (0, 0, 1.46), (0, 0, 1.68), 'neck'),
    ]
    for side, sign in (('L', 1), ('R', -1)):
        specifications.extend([
            ('clavicle.' + side, (0, 0, 1.33), (sign*.17, 0, 1.33), 'chest'),
            ('upper_arm.' + side, (sign*.17, 0, 1.33), (sign*.32, 0, 1.10), 'clavicle.' + side),
            ('forearm.' + side, (sign*.32, 0, 1.10), (sign*.43, -.015, .88), 'upper_arm.' + side),
            ('hand.' + side, (sign*.43, -.015, .88), (sign*.47, -.02, .78), 'forearm.' + side),
            ('thigh.' + side, (sign*.09, 0, .92), (sign*.092, -.025, .52), 'pelvis'),
            ('shin.' + side, (sign*.092, -.025, .52), (sign*.093, 0, .115), 'thigh.' + side),
            ('foot.' + side, (sign*.093, 0, .115), (sign*.093, -.16, .065), 'shin.' + side),
            ('toe.' + side, (sign*.093, -.16, .065), (sign*.093, -.23, .06), 'foot.' + side),
        ])
    specifications.extend([
        ('hair.01', (0, .04, 1.65), (0, .12, 1.46), 'head'),
        ('hair.02', (0, .12, 1.46), (0, .15, 1.23), 'hair.01'),
        ('hair.03', (0, .15, 1.23), (0, .12, 1.03), 'hair.02'),
    ])
    for name, head, tail, parent in specifications:
        bone = data.edit_bones.new(name)
        bone.head, bone.tail = head, tail
        if parent:
            bone.parent = data.edit_bones[parent]
            bone.use_connect = False
        bone.use_deform = name != 'root'
    bpy.ops.object.mode_set(mode='OBJECT')
    for bone in rig.pose.bones:
        bone.rotation_mode = 'XYZ'
    rig['forward_axis_blender'] = '-Y'
    rig['animation_style'] = 'in_place'
    rig['run_reference_speed_m_s'] = 2.06
    return rig


class _RunnerPose:
    """Constroi rotacoes locais FK a partir de orientacoes no espaco do rig."""

    def __init__(self, rig):
        self.rig = rig
        self.rest = {b.name: b.matrix_local.copy() for b in rig.data.bones}
        self.pose = {}

    def base(self, name):
        bone = self.rig.data.bones[name]
        if bone.parent:
            parent_name = bone.parent.name
            return self.pose[parent_name] @ self.rest[parent_name].inverted() @ self.rest[name]
        return self.rest[name].copy()

    def orient(self, name, delta, offset=None):
        """delta e a rotacao global em relacao a orientacao de descanso."""
        base = self.base(name)
        desired = delta @ self.rest[name].to_quaternion()
        local = base.to_quaternion().inverted() @ desired
        pb = self.rig.pose.bones[name]
        previous = pb.rotation_euler.copy()
        pb.rotation_euler = local.to_euler('XYZ', previous)
        pb.location = (0, 0, 0)
        pb.scale = (1, 1, 1)
        if offset is not None:
            pb.location = base.to_3x3().inverted() @ Vector(offset)
        basis = Matrix.Translation(pb.location) @ local.to_matrix().to_4x4()
        self.pose[name] = base @ basis

    def direction(self, name, direction):
        bone = self.rig.data.bones[name]
        original = (bone.tail_local - bone.head_local).normalized()
        self.orient(name, original.rotation_difference(Vector(direction).normalized()))

    def key(self, frame):
        for pb in self.rig.pose.bones:
            pb.keyframe_insert('rotation_euler', frame=frame, group=pb.name)
            pb.keyframe_insert('location', frame=frame, group=pb.name)


def _runner_rotation(x=0.0, y=0.0, z=0.0):
    return (Quaternion((0, 0, 1), math.radians(z)) @
            Quaternion((0, 1, 0), math.radians(y)) @
            Quaternion((1, 0, 0), math.radians(x)))


def _runner_foot_target(phase, sign):
    # 34% do ciclo em apoio; a velocidade de recuo e constante no apoio.
    stance = .34
    phase %= 1.0
    if phase <= stance:
        u = phase / stance
        return Vector((sign*.098, -.28 + .56*u, .127)), 0.0
    u = (phase - stance) / (1.0 - stance)
    # Hermite: preserva a velocidade horizontal nas duas passagens do apoio.
    m = (.56 / stance) * (1.0 - stance)
    y = ((2*u**3 - 3*u*u + 1)*.28 +
         (u**3 - 2*u*u + u)*m +
         (-2*u**3 + 3*u*u)*(-.28) + (u**3 - u*u)*m)
    lift = .29 * max(0.0, math.sin(math.pi*u))**1.35
    pitch = 28.0 * math.sin(2*math.pi*u)
    return Vector((sign*.098, y, .127 + lift)), pitch


def _runner_leg(pose, side, ankle, pitch):
    thigh = 'thigh.' + side
    shin = 'shin.' + side
    hip = pose.base(thigh).translation
    l1 = pose.rig.data.bones[thigh].length
    l2 = pose.rig.data.bones[shin].length
    displacement = ankle - hip
    distance = min(displacement.length, (l1+l2)*.9995)
    axis = displacement.normalized()
    # Polo do joelho para a frente (-Y), ortogonal a linha quadril/tornozelo.
    pole = Vector((0, -1, 0))
    pole = (pole - axis*axis.dot(pole)).normalized()
    along = (l1*l1 - l2*l2 + distance*distance)/(2*distance)
    bend = math.sqrt(max(0.0, l1*l1-along*along))
    knee = hip + axis*along + pole*bend
    clamped_ankle = hip + axis*distance
    pose.direction(thigh, knee-hip)
    pose.direction(shin, clamped_ankle-knee)
    pose.orient('foot.' + side, _runner_rotation(x=pitch))
    pose.orient('toe.' + side, _runner_rotation(x=pitch))


def _runner_thumb_up(pose, side, fore):
    """Gira a palma ao redor do antebraco; polegar aponta para cima.

    A direcao radial em descanso corresponde a palma do runner_model.py.
    O roll e calculado em cada quadro, evitando sinais fixos incorretos nos
    lados espelhados. Parte da torcao fica no antebraco para suavizar o pulso.
    """
    sign = 1 if side == 'L' else -1
    axis = fore.normalized()
    hand = pose.rig.data.bones['hand.' + side]
    rest_axis = (hand.tail_local-hand.head_local).normalized()
    align_hand = rest_axis.rotation_difference(axis)
    radial = align_hand @ Vector((-sign*.915, 0, -.40))
    radial = (radial-axis*radial.dot(axis)).normalized()
    up = Vector((0, 0, 1))
    up = (up-axis*up.dot(axis)).normalized()
    roll = math.atan2(axis.dot(radial.cross(up)), radial.dot(up))
    forearm = pose.rig.data.bones['forearm.' + side]
    fore_axis = (forearm.tail_local-forearm.head_local).normalized()
    align_fore = fore_axis.rotation_difference(axis)
    pose.orient('forearm.' + side, Quaternion(axis, .75*roll) @ align_fore)
    pose.orient('hand.' + side, Quaternion(axis, roll) @ align_hand)


def _runner_run_pose(rig, phase):
    pose = _RunnerPose(rig)
    angle = 2*math.pi*phase
    sway = math.sin(angle)
    pose.orient('root', _runner_rotation())
    pose.orient('pelvis', _runner_rotation(x=5, y=1.2*sway, z=2.5*sway),
                (0, 0, -.075-.012*math.cos(2*angle-.4)))
    pose.orient('spine', _runner_rotation(x=9, y=-sway, z=-sway))
    pose.orient('chest', _runner_rotation(x=11, y=-1.5*sway, z=-4*sway))
    pose.orient('neck', _runner_rotation(x=6, z=-1.5*sway))
    pose.orient('head', _runner_rotation(x=1, z=-.6*sway))
    for side, sign in (('L', 1), ('R', -1)):
        side_phase = (phase + (0 if side == 'L' else .5)) % 1.0
        ankle, pitch = _runner_foot_target(side_phase, sign)
        _runner_leg(pose, side, ankle, pitch)
        pose.orient('clavicle.' + side, _runner_rotation(x=11, z=-4*sway))
        swing = math.radians(31*math.cos(2*math.pi*side_phase-.3))
        elbow = math.radians(83 + 7*math.sin(2*math.pi*side_phase))
        upper = Vector((sign*.022, .265*math.sin(swing), -.265*math.cos(swing)))
        fore = Vector((sign*.012, .24*math.sin(swing-elbow), -.24*math.cos(swing-elbow)))
        pose.direction('upper_arm.' + side, upper)
        _runner_thumb_up(pose, side, fore)
    for i, name in enumerate(('hair.01', 'hair.02', 'hair.03')):
        pose.orient(name, _runner_rotation(x=-3+(3+i)*math.sin(2*angle-.7*i),
                                           y=2.0*math.sin(angle-.6*i)))
    return pose


def _runner_idle_pose(rig, phase):
    pose = _RunnerPose(rig)
    breath = math.sin(2*math.pi*phase)
    pose.orient('root', _runner_rotation())
    pose.orient('pelvis', _runner_rotation(), (0, 0, -.003))
    pose.orient('spine', _runner_rotation(x=.35*breath))
    pose.orient('chest', _runner_rotation(x=.7*breath))
    pose.orient('neck', _runner_rotation(x=.2*breath))
    pose.orient('head', _runner_rotation(x=-.2*breath))
    for side, sign in (('L', 1), ('R', -1)):
        for name in ('thigh.', 'shin.', 'foot.', 'toe.'):
            pose.orient(name+side, _runner_rotation())
        pose.orient('clavicle.'+side, _runner_rotation(x=.7*breath))
        pose.direction('upper_arm.'+side, (sign*.064, -.003, -.267))
        pose.direction('forearm.'+side, (sign*.03, -.018, -.245))
        pose.direction('hand.'+side, (sign*.01, -.014, -.106))
    for i, name in enumerate(('hair.01', 'hair.02', 'hair.03')):
        pose.orient(name, _runner_rotation(x=.5*math.sin(2*math.pi*phase-.4*i)))
    return pose


def _runner_curves(action):
    """Enumera F-curves via API legada ou Actions com slots do Blender 4.4+."""
    if hasattr(action, 'layers') and len(action.layers):
        for layer in action.layers:
            for strip in layer.strips:
                if hasattr(strip, 'channelbags'):
                    for bag in strip.channelbags:
                        yield from bag.fcurves
    elif hasattr(action, 'fcurves'):
        yield from action.fcurves


def create_animations(armature):
    """Retorna {'run_loop': Action, 'idle': Action}, em trilhas NLA separadas.

    Ambas ficam salvas em NLA. A trilha idle fica muda para a pre-visualizacao;
    exportadores devem coletar ACTIONS ou desmutar trilhas para exportar NLA.
    """
    scene = bpy.context.scene
    scene.render.fps = 30
    scene.render.fps_base = 1.0
    animation = armature.animation_data_create()
    actions = {}
    slots = {}
    for name, intervals, maker in (
            ('run_loop', 24, _runner_run_pose),
            ('idle', 60, _runner_idle_pose)):
        action = bpy.data.actions.new(name)
        action.use_fake_user = True
        animation.action = action
        if hasattr(action, 'slots'):
            slot = action.slots.new(id_type='OBJECT', name=armature.name)
            animation.action_slot = slot
            slots[name] = slot
        # O ultimo keyframe coincide com o primeiro; sao 24/60 intervalos.
        for index in range(intervals+1):
            maker(armature, index/intervals).key(index+1)
        for curve in _runner_curves(action):
            for key in curve.keyframe_points:
                key.interpolation = 'LINEAR'
        if hasattr(action, 'use_frame_range'):
            action.use_frame_range = True
            action.frame_start = 1
            action.frame_end = intervals+1
        action['loop_hint'] = True
        action['root_motion'] = False
        action['sample_rate_fps'] = 30
        actions[name] = action
        # NLA: um clipe por trilha, com o mesmo nome usado na exportacao.
        animation.action = None
        track = animation.nla_tracks.new()
        track.name = name
        nla = track.strips.new(name, 1, action)
        if name in slots and hasattr(nla, 'action_slot'):
            nla.action_slot = slots[name]
        nla.action_frame_start = 1
        nla.action_frame_end = intervals+1
        nla.extrapolation = 'NOTHING'
        track.mute = True  # Evita sobreposicao durante a criacao do outro clipe.
    for track in animation.nla_tracks:
        if track.name in actions:
            track.mute = track.name != 'run_loop'
    animation.action = None
    scene.frame_start, scene.frame_end = 1, 24
    scene.frame_set(1)
    bpy.context.view_layer.update()
    return actions


"""Corre pro Ponto: animacao corporal FK/IK e cabelo PBD gravado em keyframes.

Fisica aproximada: cadeia inextensivel, gravidade, amortecimento e colisoes
esfericas/capsulares. Nao e uma simulacao de cada fio nem substitui fisica runtime.
"""

FPS = 30
RUN_SECONDS = .8
RUN_SPEED = .56 / (.34 * RUN_SECONDS)
LANE_WIDTH = .65
LANE_SECONDS = .8
GRAVITY = 9.81
HAIR_NAMES = ('hair.01', 'hair.02', 'hair.03')


def _ease(t):
    t = max(0., min(1., t))
    return t*t*t*(10. + t*(-15. + 6.*t))


def _pose_snapshot(rig):
    return {p.name: (p.location.copy(), p.rotation_euler.to_quaternion())
            for p in rig.pose.bones}


def _from_snapshot(rig, values):
    pose = _RunnerPose(rig)
    for bone in rig.data.bones:
        pb = rig.pose.bones[bone.name]
        loc, quat = values[bone.name]
        pb.location = loc
        pb.rotation_euler = quat.to_euler('XYZ', pb.rotation_euler)
        pb.scale = (1, 1, 1)
        pose.pose[bone.name] = pose.base(bone.name) @ (Matrix.Translation(loc) @ quat.to_matrix().to_4x4())
    return pose


def _mix_poses(rig, first, second, amount):
    pa = _from_snapshot(rig, first)
    ankles_a = {s: pa.pose['foot.'+s].translation.copy() for s in ('L','R')}
    pb = _from_snapshot(rig, second)
    ankles_b = {s: pb.pose['foot.'+s].translation.copy() for s in ('L','R')}
    pose = _from_snapshot(rig, {name: (first[name][0].lerp(second[name][0], amount),
        first[name][1].slerp(second[name][1], amount)) for name in first})
    # Misturar somente FK faz os pes afundarem durante a flexao da pelve.
    # Resolve novamente os joelhos e tornozelos para a trajetoria de contato.
    for side in ('L','R'):
        rotations = {n: pose.pose[n].to_quaternion() @ pose.rest[n].to_quaternion().inverted()
                     for n in ('foot.'+side, 'toe.'+side)}
        _leg(pose, side, ankles_a[side].lerp(ankles_b[side], amount))
        for name, rotation in rotations.items():
            pose.orient(name, rotation)
    return pose


def _ground_height(pitch):
    # Limite conservador do solado em relacao ao tornozelo: evita atravessar o piso.
    angle = math.radians(pitch)
    return .103 * math.cos(angle) + (.235 if angle >= 0 else .057) * abs(math.sin(angle))


def _runner_foot_target(phase, sign):
    phase %= 1.
    stance = .34
    if phase <= stance:
        u = phase / stance
        return Vector((sign*.098, -.28 + .56*u, .103)), 0.
    u = (phase - stance) / (1 - stance)
    m = (.56 / stance) * (1 - stance)
    y = ((2*u**3 - 3*u*u + 1)*.28 + (u**3 - 2*u*u + u)*m
         + (-2*u**3 + 3*u*u)*(-.28) + (u**3-u*u)*m)
    pitch = 20. * math.sin(2*math.pi*u)
    lift = .25 * max(0., math.sin(math.pi*u))**1.35
    return Vector((sign*.098, y, _ground_height(pitch) + lift)), pitch


def _leg(pose, side, ankle, pitch=0., yaw=0.):
    thigh, shin = 'thigh.' + side, 'shin.' + side
    hip = pose.base(thigh).translation
    l1, l2 = pose.rig.data.bones[thigh].length, pose.rig.data.bones[shin].length
    displacement = ankle - hip
    distance = min(max(displacement.length, .001), (l1+l2)*.9995)
    axis = displacement.normalized()
    pole = _runner_rotation(z=yaw) @ Vector((0, -1, 0))
    pole = (pole - axis*axis.dot(pole)).normalized()
    along = (l1*l1 - l2*l2 + distance*distance)/(2*distance)
    knee = hip + axis*along + pole*math.sqrt(max(0., l1*l1-along*along))
    pose.direction(thigh, knee-hip)
    pose.direction(shin, hip+axis*distance-knee)
    pose.orient('foot.'+side, _runner_rotation(x=pitch, z=yaw))
    pose.orient('toe.'+side, _runner_rotation(x=pitch, z=yaw))


def _neutral_hair(pose):
    # O solver vai substituir estas rotacoes; serve somente para completar a pose.
    head_delta = pose.pose['head'].to_quaternion() @ pose.rest['head'].to_quaternion().inverted()
    for name in HAIR_NAMES:
        pose.orient(name, head_delta)
    return pose


def _torso(pose, drop=-.075, lean=10., sway=0., yaw=0., side_lean=0., back=0.):
    pose.orient('root', _runner_rotation())
    pose.orient('pelvis', _runner_rotation(x=lean*.45, y=side_lean, z=yaw*.55+2.5*sway), (0, back, drop))
    pose.orient('spine', _runner_rotation(x=lean*.8, y=side_lean*.85, z=yaw*.75-sway))
    pose.orient('chest', _runner_rotation(x=lean, y=side_lean*.7, z=yaw-4*sway))
    pose.orient('neck', _runner_rotation(x=lean*.45, y=side_lean*.45, z=yaw*.65-sway))
    pose.orient('head', _runner_rotation(x=lean*.12, y=side_lean*.2, z=yaw*.35))


def _arms(pose, phase, lean=10., yaw=0., amplitude=30., bend=86., balance=0.):
    q = _runner_rotation(z=yaw)
    for side, sign in (('L', 1), ('R', -1)):
        p = phase + (0 if side == 'L' else .5)
        pose.orient('clavicle.'+side, _runner_rotation(x=lean, z=yaw))
        swing = math.radians(amplitude*math.cos(2*math.pi*p-.3))
        elbow = math.radians(bend+6*math.sin(2*math.pi*p))
        upper = q @ Vector((sign*(.022+balance), .265*math.sin(swing), -.265*math.cos(swing)))
        fore = q @ Vector((sign*.012, .24*math.sin(swing-elbow), -.24*math.cos(swing-elbow)))
        pose.direction('upper_arm.'+side, upper)
        _runner_thumb_up(pose, side, fore)


def _run_body(rig, phase):
    pose = _RunnerPose(rig)
    angle = 2*math.pi*phase
    _torso(pose, -.085-.010*math.cos(2*angle-.4), 10., math.sin(angle))
    for side, sign in (('L', 1), ('R', -1)):
        ankle, pitch = _runner_foot_target(phase+(0 if side=='L' else .5), sign)
        _leg(pose, side, ankle, pitch)
    _arms(pose, phase)
    return _neutral_hair(pose)


def _idle_body(rig, phase):
    pose = _runner_idle_pose(rig, phase)
    # Original sola em z=.012: baixar 12mm alinha os pes ao chao.
    values = _pose_snapshot(rig)
    values['pelvis'] = (values['pelvis'][0] + pose.base('pelvis').to_3x3().inverted() @ Vector((0, 0, -.009)), values['pelvis'][1])
    return _neutral_hair(_from_snapshot(rig, values))


def _crouch_body(rig, phase, stepping=False):
    pose = _RunnerPose(rig)
    a = 2*math.pi*phase
    _torso(pose, -.30 + (.007*math.cos(2*a) if stepping else .0015*math.sin(a)),
           33.+.7*math.sin(a), .2*math.sin(a), back=.065)
    for side, sign in (('L', 1), ('R', -1)):
        p = (phase+(0 if side=='L' else .5)) % 1
        y, z = -.04, .103
        if stepping:
            if p <= .60:
                y = -.17 + .34*p/.60
            else:
                u = (p-.60)/.40
                y = .17-.34*_ease(u)
                z += .065*math.sin(math.pi*u)
        _leg(pose, side, Vector((sign*.116, y, z)))
    for side, sign in (('L', 1), ('R', -1)):
        pose.orient('clavicle.'+side, _runner_rotation(x=27))
        swing = .025*math.sin(a+(0 if side=='L' else math.pi)) if stepping else 0
        pose.direction('upper_arm.'+side, Vector((sign*.035, -.14+swing, -.22)))
        _runner_thumb_up(pose, side, Vector((sign*.015, -.205, .035)))
    return _neutral_hair(pose)


def _transition(rig, phase, reverse=False):
    _run_body(rig, 0)
    a = _pose_snapshot(rig)
    _crouch_body(rig, 0)
    b = _pose_snapshot(rig)
    return _mix_poses(rig, a, b, 1-_ease(phase) if reverse else _ease(phase))


def _jump_contact(rig, compression=0.):
    pose = _RunnerPose(rig)
    _torso(pose, -.035-.20*compression, 9.+15*compression, back=.02*compression)
    for side, sign in (('L', 1), ('R', -1)):
        _leg(pose, side, Vector((sign*.102, -.02 if side=='L' else .015, .103)))
        pose.orient('clavicle.'+side, _runner_rotation(x=14))
        pose.direction('upper_arm.'+side, Vector((sign*.034, -.10-.07*compression, -.24)))
        _runner_thumb_up(pose, side, Vector((sign*.012, -.18, .12)))
    return _neutral_hair(pose)


def _jump_air(rig, phase):
    pose = _RunnerPose(rig)
    breath = math.sin(2*math.pi*phase)
    _torso(pose, -.015, 12.+breath, .15*breath)
    for side, sign in (('L', 1), ('R', -1)):
        _leg(pose, side, Vector((sign*.105, .11 if side=='L' else .22, .34 if side=='L' else .44)), -10.)
        pose.orient('clavicle.'+side, _runner_rotation(x=13))
        pose.direction('upper_arm.'+side, Vector((sign*.045, -.13, -.22)))
        _runner_thumb_up(pose, side, Vector((sign*.015, -.13, .19)))
    return _neutral_hair(pose)


def _jump_start(rig, phase):
    # Impulso: flexao preparatoria seguida de extensao e bracos para a frente.
    _run_body(rig, 0)
    a = _pose_snapshot(rig)
    _jump_contact(rig, .50*math.sin(math.pi*phase))
    b = _pose_snapshot(rig)
    return _mix_poses(rig, a, b, _ease(min(1., phase*2)))


def _jump_fall(rig, phase):
    _jump_air(rig, 0)
    a = _pose_snapshot(rig)
    _jump_contact(rig, 0)
    return _mix_poses(rig, a, _pose_snapshot(rig), _ease(phase))


def _jump_land(rig, phase):
    _jump_contact(rig, math.sin(math.pi*min(1., phase/.72))*.72)
    a = _pose_snapshot(rig)
    _run_body(rig, 0)
    b = _pose_snapshot(rig)
    return _mix_poses(rig, a, b, _ease((phase-.55)/.45))


def _jump_full(rig, phase):
    t = phase*1.2
    height = 0.
    if t < .2:
        pose = _jump_start(rig, t/.2)
    elif t < .92:
        f = t-.2
        height = .5*GRAVITY*f*(.72-f)
        if f < .15:
            _jump_contact(rig, 0)
            a = _pose_snapshot(rig)
            _jump_air(rig, 0)
            pose = _mix_poses(rig, a, _pose_snapshot(rig), _ease(f/.15))
        elif f > .54:
            pose = _jump_fall(rig, (f-.54)/.18)
        else:
            pose = _jump_air(rig, (f-.15)/.39)
    else:
        pose = _jump_land(rig, (t-.92)/.28)
    values = _pose_snapshot(rig)
    values['root'] = (rig.data.bones['root'].matrix_local.to_3x3().inverted() @ Vector((0, 0, height)), values['root'][1])
    return _from_snapshot(rig, values)


def _lane_x(t, sign):
    return sign*LANE_WIDTH*_ease(t/LANE_SECONDS)


def _lane_body(rig, phase, sign):
    t = phase*LANE_SECONDS
    phase_run = t/RUN_SECONDS
    x = _lane_x(t, sign)
    dt = .002
    vx = (_lane_x(t+dt, sign)-_lane_x(t-dt, sign))/(2*dt)
    ax = (_lane_x(t+dt, sign)-2*x+_lane_x(t-dt, sign))/(dt*dt)
    yaw = math.degrees(math.atan2(vx, RUN_SPEED))*.72
    lean = max(-16., min(16., math.degrees(math.atan2(ax, GRAVITY))*.65))
    pose = _RunnerPose(rig)
    _torso(pose, -.085-.040*math.sin(math.pi*phase)**2,
           10., math.sin(2*math.pi*phase_run), yaw, lean)
    for side, lateral in (('L', 1), ('R', -1)):
        p = (phase_run+(0 if side=='L' else .5)) % 1
        ankle, pitch = _runner_foot_target(p, lateral)
        tc = t-p*RUN_SECONDS
        plant_a = _lane_x(tc+.136, sign)+lateral*.098
        if p <= .34:
            target_x = plant_a-x
        else:
            plant_b = _lane_x(tc+RUN_SECONDS+.136, sign)+lateral*.098
            target_x = plant_a+(plant_b-plant_a)*_ease((p-.34)/.66)-x
        ankle.x = max(-.30, min(.30, target_x))
        _leg(pose, side, ankle, pitch, yaw*.6)
    _arms(pose, phase_run, yaw=yaw, amplitude=25., balance=.025*math.sin(math.pi*phase))
    return _neutral_hair(pose)


def _lane_motion(rig, phase, sign):
    _lane_body(rig, phase, sign)
    values = _pose_snapshot(rig)
    # Copia de demonstracao com deslocamento lateral; movimento frontal segue no jogo.
    values['root'] = (rig.data.bones['root'].matrix_local.to_3x3().inverted() @ Vector((_lane_x(phase*LANE_SECONDS, sign), 0, 0)), values['root'][1])
    return _from_snapshot(rig, values)


def _deformed_point(pose, bone, rest_point):
    return pose.pose[bone] @ pose.rest[bone].inverted() @ Vector(rest_point)


def _colliders(pose):
    return [(_deformed_point(pose, 'head', (0, .012, 1.567)),
             _deformed_point(pose, 'head', (0, .012, 1.567)), .088),
            (_deformed_point(pose, 'chest', (0, .015, 1.20)),
             _deformed_point(pose, 'chest', (0, .015, 1.33)), .101),
            (_deformed_point(pose, 'spine', (0, .035, 1.05)),
             _deformed_point(pose, 'spine', (0, .025, 1.18)), .084)]


class _HairPhysics:
    """Verlet/PBD a 120Hz; comprimentos fixos, atrito viscoso e barreiras corporais."""
    def __init__(self, rig, pose, shift):
        self.lengths = [rig.data.bones[n].length for n in HAIR_NAMES]
        self.points = [pose.base(HAIR_NAMES[0]).translation+shift]
        for name in HAIR_NAMES:
            self.points.append(pose.pose[name] @ Vector((0, rig.data.bones[name].length, 0))+shift)
        self.previous = [p.copy() for p in self.points]
        self.max_length_error = 0.

    def step(self, anchor, rest_dirs, colliders, dt):
        old = [p.copy() for p in self.points]
        self.points[0] = anchor.copy()
        for i in range(1, 4):
            velocity = (self.points[i]-self.previous[i])/dt
            # Gravidade em m/s²; arrasto aproxima resistencia do ar.
            acceleration = Vector((0, 0, -GRAVITY)) - velocity*(.9+.20*velocity.length)
            desired = self.points[i-1] + rest_dirs[i-1]*self.lengths[i-1]
            acceleration += (desired-self.points[i]) * (32., 20., 13.)[i-1]
            self.points[i] += velocity*dt + acceleration*dt*dt
        self.previous = old
        for _ in range(12):
            self.points[0] = anchor.copy()
            for i in range(1, 4):
                delta = self.points[i]-self.points[i-1]
                direction = delta.normalized() if delta.length > 1e-8 else rest_dirs[i-1]
                # Limita curvatura extrema; o cabelo pode balancar, mas nao inverter.
                axis = rest_dirs[i-1]
                angle = axis.angle(direction, 0.)
                if angle > math.radians(72):
                    direction = axis.lerp(direction, math.radians(72)/angle).normalized()
                self.points[i] = self.points[i-1]+direction*self.lengths[i-1]
                for a, b, radius in colliders:
                    ab = b-a
                    u = max(0., min(1., (self.points[i]-a).dot(ab)/ab.length_squared)) if ab.length_squared > 1e-9 else 0.
                    center = a+ab*u
                    delta = self.points[i]-center
                    limit = radius+.028
                    if delta.length < limit:
                        normal = delta.normalized() if delta.length > 1e-8 else Vector((0, 1, 0))
                        self.points[i] = center+normal*limit
        # Ultima projecao assegura que os ossos nao estiquem.
        for i in range(1, 4):
            self.points[i] = self.points[i-1]+(self.points[i]-self.points[i-1]).normalized()*self.lengths[i-1]


def _physical_hair(rig, poses, seconds, loop, virtual_shift):
    intervals = len(poses)-1
    substeps = 4
    dt = 1/(FPS*substeps)
    cache = []
    for values in poses:
        pose = _from_snapshot(rig, values)
        cache.append((pose.base(HAIR_NAMES[0]).translation.copy(),
                      [(pose.pose[n].to_3x3() @ Vector((0, 1, 0))).normalized() for n in HAIR_NAMES],
                      _colliders(pose)))
    warm = intervals*substeps*7 if loop else FPS*substeps*2
    initial_t = -warm*dt
    p0 = _from_snapshot(rig, poses[0])
    physics = _HairPhysics(rig, p0, virtual_shift(initial_t))
    saved = []
    # Inclui o primeiro sample; a etapa anterior aquece o sistema fisico.
    for step in range(-warm, intervals*substeps+1):
        t = step*dt
        f = ((t % seconds)*FPS) if loop else max(0., min(intervals, t*FPS))
        lo = min(intervals-1, int(f))
        alpha = f-lo
        a, b = cache[lo], cache[lo+1]
        shift = virtual_shift(t)
        anchor = a[0].lerp(b[0], alpha)+shift
        dirs = [u.lerp(v, alpha).normalized() for u, v in zip(a[1], b[1])]
        cols = [(c[0].lerp(d[0], alpha)+shift, c[1].lerp(d[1], alpha)+shift, c[2])
                for c, d in zip(a[2], b[2])]
        physics.step(anchor, dirs, cols, dt)
        if step >= 0 and step % substeps == 0:
            idx = step//substeps
            pose = _from_snapshot(rig, poses[idx])
            for i, name in enumerate(HAIR_NAMES):
                pose.direction(name, physics.points[i+1]-physics.points[i])
            saved.append(_pose_snapshot(rig))
    # Remove erro residual de fechamento apenas em ciclos periodicos.
    if loop:
        for name in HAIR_NAMES:
            first, last = saved[0][name][1], saved[-1][name][1]
            correction = last.inverted() @ first
            for i, values in enumerate(saved):
                q = values[name][1] @ Quaternion().slerp(correction, i/intervals)
                values[name] = (values[name][0], q)
        saved[-1] = {name: (loc.copy(), q.copy()) for name, (loc, q) in saved[0].items()}
    return saved


def animation_specs():
    forward = lambda t: Vector((0, -RUN_SPEED*t, 0))
    still = lambda t: Vector((0, 0, 0))
    lane = lambda sign: lambda t: Vector((_lane_x(t, sign), -RUN_SPEED*t, 0))
    return [
        ('idle', 60, _idle_body, True, still, 'none'),
        ('run_loop', 24, _run_body, True, forward, 'none'),
        ('jump_start', 6, _jump_start, False, forward, 'none'),
        ('jump_air', 18, _jump_air, True, forward, 'none'),
        ('jump_fall', 6, _jump_fall, False, forward, 'none'),
        ('jump_land', 9, _jump_land, False, forward, 'none'),
        ('jump_full_motion', 36, _jump_full, False, forward, 'vertical_preview'),
        ('crouch_enter', 9, lambda r,p: _transition(r,p), False, forward, 'none'),
        ('crouch_loop', 36, _crouch_body, True, still, 'none'),
        ('crouch_run_loop', 24, lambda r,p: _crouch_body(r,p,True), True,
            lambda t: Vector((0, -.34/(.60*.8)*t, 0)), 'none'),
        ('crouch_exit', 9, lambda r,p: _transition(r,p,True), False, forward, 'none'),
        ('lane_left', 24, lambda r,p: _lane_body(r,p,1), False, lane(1), 'none'),
        ('lane_right', 24, lambda r,p: _lane_body(r,p,-1), False, lane(-1), 'none'),
        ('lane_left_motion', 24, lambda r,p: _lane_motion(r,p,1), False, forward, 'lateral_preview'),
        ('lane_right_motion', 24, lambda r,p: _lane_motion(r,p,-1), False, forward, 'lateral_preview'),
    ]


def create_animations(armature):
    scene = bpy.context.scene
    scene.render.fps, scene.render.fps_base = FPS, 1.
    ad = armature.animation_data_create()
    actions = {}
    for name, intervals, maker, loop, shift, root_mode in animation_specs():
        print('BAKING_CLIP', name, flush=True)
        ad.action = None
        for track in ad.nla_tracks:
            track.mute = True
        poses = []
        for i in range(intervals+1):
            maker(armature, i/intervals)
            poses.append(_pose_snapshot(armature))
        poses = _physical_hair(armature, poses, intervals/FPS, loop, shift)
        action = bpy.data.actions.new(name)
        action.use_fake_user = True
        ad.action = action
        slot = None
        if hasattr(action, 'slots'):
            slot = action.slots.new(id_type='OBJECT', name=armature.name)
            ad.action_slot = slot
        for i, values in enumerate(poses):
            _from_snapshot(armature, values).key(i+1)
        for curve in _runner_curves(action):
            for key in curve.keyframe_points:
                key.interpolation = 'LINEAR'
        action.use_frame_range = True
        action.frame_start, action.frame_end = 1, intervals+1
        action['loop_hint'], action['root_motion'] = loop, root_mode
        action['hair_physics'] = 'PBD_120Hz_gravity_inertia_drag_body_colliders'
        action['sample_rate_fps'] = FPS
        actions[name] = action
        ad.action = None
        track = ad.nla_tracks.new()
        track.name = name
        strip = track.strips.new(name, 1, action)
        if slot and hasattr(strip, 'action_slot'):
            strip.action_slot = slot
        strip.action_frame_start, strip.action_frame_end = 1, intervals+1
        strip.extrapolation = 'NOTHING'
        track.mute = True
    armature['run_reference_speed_m_s'] = RUN_SPEED
    armature['hair_simulation'] = 'baked PBD; runtime physics requires Godot modifier'
    scene.frame_start, scene.frame_end = 1, 24
    scene.frame_set(1)
    return actions


def create_demo_sequence(rig, actions, scene):
    """Sequencia so do .blend: Play mostra todas as movimentacoes sem configurar NLA."""
    segments = [('run_loop',24,0.), ('run_loop',24,0.), ('jump_full_motion',36,0.),
        ('crouch_enter',9,0.), ('crouch_loop',36,0.), ('crouch_exit',9,0.),
        ('lane_left_motion',24,0.), ('lane_right_motion',24,LANE_WIDTH)]
    samples = []
    labels = []
    for name, count, offset_x in segments:
        select_action(rig, actions[name])
        labels.append((len(samples)+1,name))
        for i in range(count):
            scene.frame_set(i+1)
            values = _pose_snapshot(rig)
            location, rotation = values['root']
            values['root'] = (location+rig.data.bones['root'].matrix_local.to_3x3().inverted() @ Vector((offset_x,0,0)), rotation)
            samples.append(values)
    ad = rig.animation_data
    action = bpy.data.actions.new('DEMO_todas_animacoes_NAO_EXPORTAR')
    action.use_fake_user = True
    ad.action = action
    slot = action.slots.new(id_type='OBJECT', name=rig.name)
    ad.action_slot = slot
    for i, values in enumerate(samples):
        _from_snapshot(rig, values).key(i+1)
    for curve in _runner_curves(action):
        for key in curve.keyframe_points:
            key.interpolation = 'LINEAR'
    for frame,name in labels:
        marker = scene.timeline_markers.new(name, frame=frame)
    action.use_frame_range = True
    action.frame_start, action.frame_end = 1, len(samples)
    scene.frame_start, scene.frame_end = 1, len(samples)
    return action


"""Gerador procedural de uma personagem runner. Blender 4.2+ / testado em 5.2.

No Blender: Scripting > Open > selecione este .py > Run Script (Alt+P).
O script cria uma NOVA cena e uma pasta de saída exclusiva; não limpa sua cena.
Os assets são originais e procedurais. Acabamento de base estilizada/semi-realista.
"""
import bpy
import math
import json
import sys
import argparse
from pathlib import Path
from datetime import datetime
from mathutils import Vector
from math import sin, cos, pi
import numpy as np

# Pode alterar estes valores antes de executar.
OUTPUT_DIR = ""  # Vazio: pasta personagem_runner ao lado deste script.
RENDER_PREVIEWS = True
TEXTURE_SIZE = 512
PREFIX = 'Runner_'


def linear(c):
    return c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4


def rgb(code):
    return tuple(linear(int(code[i:i + 2], 16) / 255) for i in (0, 2, 4))


class Geometry:
    """Uma malha por material, com pesos explícitos e cores por vértice."""
    def __init__(self, name, material):
        self.name, self.material = name, material
        self.verts, self.faces, self.uvs, self.colors, self.weights = [], [], [], [], []

    def vertex(self, p, uv, color, weights):
        self.verts.append(tuple(p))
        self.uvs.append(uv)
        self.colors.append((*rgb(color), 1.0))
        self.weights.append(weights)
        return len(self.verts) - 1

    def loft(self, rings, sides, color, weight_fn, caps=True):
        # rings = (centro, eixo de raio 1, eixo de raio 2, raio 1, raio 2)
        base = len(self.verts)
        for j, (center, axis1, axis2, r1, r2) in enumerate(rings):
            center, axis1, axis2 = Vector(center), Vector(axis1), Vector(axis2)
            for k in range(sides + 1):
                a = 2 * pi * k / sides
                p = center + axis1 * (r1 * cos(a)) + axis2 * (r2 * sin(a))
                self.vertex(p, (k / sides, j / max(1, len(rings) - 1)), color, weight_fn(p, j))
        for j in range(len(rings) - 1):
            for k in range(sides):
                a = base + j * (sides + 1) + k
                self.faces.append((a, a + 1, a + sides + 2, a + sides + 1))
        if caps:
            self.faces.append(tuple(base + k for k in reversed(range(sides))))
            off = base + (len(rings) - 1) * (sides + 1)
            self.faces.append(tuple(off + k for k in range(sides)))

    def vertical(self, profiles, color, weights, sides=24):
        rings = [((x, y, z), (1, 0, 0), (0, 1, 0), rx, ry) for z, x, y, rx, ry in profiles]
        self.loft(rings, sides, color, weights)

    def tube(self, points, radii, color, weights, sides=8, flatten=1.0):
        pts = [Vector(p) for p in points]
        rings = []
        for j, p in enumerate(pts):
            direction = pts[min(j + 1, len(pts) - 1)] - pts[max(j - 1, 0)]
            direction.normalize()
            ref = Vector((0, 1, 0))
            if abs(direction.dot(ref)) > .94:
                ref = Vector((1, 0, 0))
            axis1 = ref.cross(direction).normalized()
            axis2 = direction.cross(axis1).normalized()
            radius = radii[j] if isinstance(radii, (list, tuple)) else radii
            rings.append((p, axis1, axis2, radius, radius * flatten))
        self.loft(rings, sides, color, weights)

    def ellipsoid(self, center, size, color, weights, sides=16, steps=10):
        cx, cy, cz = center
        sx, sy, sz = size
        rings = []
        for j in range(steps + 1):
            a = -pi / 2 + pi * j / steps
            r = max(.002, cos(a))
            rings.append(((cx, cy, cz + sz * sin(a)), (1, 0, 0), (0, 1, 0), sx * r, sy * r))
        self.loft(rings, sides, color, weights)

    def build(self, collection, rig):
        mesh = bpy.data.meshes.new(self.name)
        mesh.from_pydata(self.verts, [], self.faces)
        mesh.update()
        # Recalcula orientação sem deixar Blender em Edit Mode.
        import bmesh
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        bm.to_mesh(mesh)
        bm.free()
        obj = bpy.data.objects.new(self.name, mesh)
        collection.objects.link(obj)
        mesh.materials.append(self.material)
        uv = mesh.uv_layers.new(name='UVMap')
        colors = mesh.color_attributes.new(name='Color', type='FLOAT_COLOR', domain='POINT')
        for i, col in enumerate(self.colors):
            colors.data[i].color = col
        mesh.color_attributes.active_color = colors
        for poly in mesh.polygons:
            poly.use_smooth = True
            for li in poly.loop_indices:
                uv.data[li].uv = self.uvs[mesh.loops[li].vertex_index]
        groups = {bone.name: obj.vertex_groups.new(name=bone.name) for bone in rig.data.bones}
        for i, weights in enumerate(self.weights):
            total = sum(weights.values())
            for bone, value in weights.items():
                if value > 1e-6:
                    groups[bone].add([i], value / total, 'REPLACE')
        # Solda costuras coincidentes preservando UVs, cores e pesos como custom data.
        # Isto une a bifurcação do short e evita vincos artificiais na linha de UV.
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=0.000001)
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        bm.to_mesh(mesh)
        bm.free()
        mesh.update()
        modifier = obj.modifiers.new('Deformacao', 'ARMATURE')
        modifier.object = rig
        obj.parent = rig
        return obj


def fixed(bone):
    return lambda p, j: {bone: 1.0}


def blend_z(z, anchors):
    anchors = sorted(anchors)
    if z <= anchors[0][0]:
        return {anchors[0][1]: 1.0}
    for (lo, a), (hi, b) in zip(anchors, anchors[1:]):
        if z <= hi:
            t = (z - lo) / (hi - lo)
            if a == b:
                return {a: 1.0}
            return {a: 1 - t, b: t}
    return {anchors[-1][1]: 1.0}


def texture_material(name, style, roughness):
    """Base-color image multiplicada por vertex color, exportável por glTF."""
    n = TEXTURE_SIZE
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    rng = np.random.default_rng(704)
    noise = rng.random((n, n), dtype=np.float32)
    if style == 'fabric':
        value = .91 + .035 * np.sin(xx * pi) + .024 * np.cos(yy * pi / 2) + .04 * noise
    elif style == 'hair':
        value = .87 + .08 * np.sin(xx * 2 * pi / 11) ** 2 + .035 * noise
    else:
        value = .955 + .03 * noise
    pixels = np.ones((n, n, 4), dtype=np.float32)
    pixels[:, :, :3] = value[:, :, None]
    im = bpy.data.images.new(name + '_detail', width=n, height=n, alpha=False)
    im.pixels.foreach_set(pixels.ravel())
    im.file_format = 'PNG'
    im.pack()
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Roughness'].default_value = roughness
    bsdf.inputs['Metallic'].default_value = 0
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    tex = nodes.new('ShaderNodeTexImage')
    tex.image = im
    tex.location = (-500, 70)
    color = nodes.new('ShaderNodeVertexColor')
    color.layer_name = 'Color'
    color.location = (-500, -100)
    mul = nodes.new('ShaderNodeMixRGB')
    mul.blend_type = 'MULTIPLY'
    mul.inputs[0].default_value = 1
    mul.location = (-220, 70)
    links.new(tex.outputs['Color'], mul.inputs[1])
    links.new(color.outputs['Color'], mul.inputs[2])
    links.new(mul.outputs[0], bsdf.inputs['Base Color'])
    mat.diffuse_color = (.25, .15, .35, 1)
    mat.use_backface_culling = True
    return mat


def make_character(collection, rig):
    skin = Geometry(PREFIX + 'Pele', texture_material('Pele', 'skin', .58))
    cloth = Geometry(PREFIX + 'Roupa_Tenis', texture_material('Roupa', 'fabric', .76))
    hair = Geometry(PREFIX + 'Trancas', texture_material('Cabelo', 'hair', .74))
    skin_color = 'a87353'
    shirt_color = '622b99'
    shorts_color = '20202b'
    hair_color = '201815'

    torso_weights = lambda p, j: blend_z(p.z, [(.97, 'pelvis'), (1.09, 'spine'), (1.25, 'chest'), (1.4, 'chest')])
    # Camiseta com cintura, tórax e ombros definidos pela própria malha.
    cloth.vertical([
        (1.00, 0, .002, .120, .077), (1.025, 0, 0, .118, .076),
        (1.07, 0, -.001, .111, .073), (1.12, 0, -.004, .114, .075),
        (1.17, 0, -.008, .129, .085), (1.22, 0, -.013, .146, .094),
        (1.265, 0, -.009, .157, .091), (1.30, 0, -.004, .169, .074),
        (1.325, 0, 0, .180, .059), (1.346, 0, .002, .150, .052),
        (1.367, 0, 0, .061, .047), (1.373, 0, 0, .052, .041)
    ], shirt_color, torso_weights, 32)
    # Bainhas, gola e costuras discretas (geometria muito leve).
    for z, rx, ry, col in [(1.008, .121, .078, '442265'), (1.018, .12, .077, '7d45ad'), (1.372, .054, .042, '472269')]:
        cloth.vertical([(z - .002, 0, 0, rx, ry), (z + .002, 0, 0, rx, ry)], col, torso_weights, 32)
    cloth.vertical([
        (.91, 0, .01, .163, .103), (.93, 0, .01, .160, .102), (.97, 0, .004, .140, .087),
        (1.002, 0, .001, .121, .078), (1.017, 0, .001, .12, .077)
    ], shorts_color, fixed('pelvis'), 20)
    # Remove a tampa inferior da cintura: as duas pernas fecham esta abertura.
    cloth.faces.pop(-2)
    cloth.vertical([(1.0, 0, .001, .122, .079), (1.019, 0, .001, .121, .078)], '15151e', fixed('pelvis'), 32)

    for side, sign in [('L', 1), ('R', -1)]:
        thigh, shin, foot = 'thigh.' + side, 'shin.' + side, 'foot.' + side
        upper, fore, hand = 'upper_arm.' + side, 'forearm.' + side, 'hand.' + side
        # Pernas contínuas com transições de pesos apenas na vizinhança do joelho.
        legw = lambda p, j, a=thigh, b=shin, c=foot: blend_z(p.z, [(.11, c), (.16, b), (.46, b), (.58, a), (.92, a)])
        skin.vertical([
            (.115, sign * .093, 0, .022, .025), (.16, sign * .094, .003, .025, .029),
            (.24, sign * .096, .012, .036, .043), (.32, sign * .099, .014, .046, .050),
            (.40, sign * .099, .001, .043, .045), (.48, sign * .094, -.016, .034, .035),
            (.52, sign * .092, -.025, .035, .038), (.57, sign * .09, -.019, .044, .049),
            (.66, sign * .09, -.008, .058, .065), (.75, sign * .089, .001, .071, .079),
            (.78, sign * .089, .004, .074, .082)
        ], skin_color, legw, 20)
        # Bifurcação da malha do short: cintura -> gancho -> pernas.
        # A costura interna compartilha a posição e os pesos no plano central.
        base = len(cloth.verts)
        for j, t in enumerate((0, .28, .58, .83, 1)):
            for k in range(21):
                a = -pi / 2 + 2 * pi * k / 20
                if k <= 10:
                    top = Vector((sign * .163 * cos(a), .01 + .103 * sin(a), .91))
                else:
                    u = (k - 10) / 10
                    top = Vector((0, .113 - .206 * u, .91 - .065 * sin(pi * u)))
                bottom = Vector((sign * (.089 + .076 * cos(a)), .002 + .084 * sin(a), .754))
                pos = top.lerp(bottom, t)
                leg_weight = _ease(min(1., t/.60))
                cloth.vertex(pos, (k / 20, t), shorts_color, {'pelvis': 1 - leg_weight, thigh: leg_weight})
        for j in range(4):
            for k in range(20):
                a = base + j * 21 + k
                cloth.faces.append((a, a + 1, a + 22, a + 21))
        cloth.vertical([(.753, sign * .089, .002, .077, .085), (.761, sign * .089, .002, .077, .085)], '393140', fixed(thigh), 20)
        # Meias curtas.
        cloth.vertical([(.095, sign * .093, 0, .027, .029), (.15, sign * .093, 0, .026, .03), (.159, sign * .093, 0, .026, .03)], '30263c', fixed(foot), 16)
        # Tênis modelado por seções transversais: calcanhar -> biqueira.
        shoe_sections = [(.057, .016, .067, .033), (.035, .037, .077, .047), (-.018, .042, .075, .048), (-.070, .046, .063, .037), (-.14, .049, .052, .029), (-.195, .046, .048, .023), (-.223, .032, .046, .019), (-.235, .01, .045, .012)]
        shoe_rings = [((sign * .093, y, z), (1, 0, 0), (0, 0, 1), width, height) for y, width, z, height in shoe_sections]
        cloth.loft(shoe_rings, 16, '513273', fixed(foot))
        sole_sections = [(y, w * 1.04, .025, .012) for y, w, z, h in shoe_sections]
        cloth.loft([((sign * .093, y, z), (1, 0, 0), (0, 0, 1), w, h) for y, w, z, h in sole_sections], 16, 'b1b8c5', fixed(foot))
        cloth.loft([((sign * .093, y, .016), (1, 0, 0), (0, 0, 1), w, .004) for y, w, z, h in sole_sections], 12, '30283b', fixed(foot))
        for j in range(4):
            y = -.025 - j * .024
            z = .117 - j * .011
            cloth.tube([(sign * .093 - .022, y, z), (sign * .093, y - .004, z + .002), (sign * .093 + .022, y, z)], .0021, '9aa6ca', fixed(foot), 5)
        # Painel lateral azul, sem logos.
        for outer in [-1, 1]:
            xx = sign * .093 + outer * .045
            cloth.tube([(xx, -.125, .061), (xx, -.081, .074), (xx * .995, -.023, .097)], [.006, .008, .006], '516f9f', fixed(foot), 5)
        # Braço inteiro: a malha atravessa cotovelo sem partes rígidas desconectadas.
        shoulder = Vector((sign * .17, 0, 1.33))
        elbow = Vector((sign * .32, 0, 1.10))
        wrist = Vector((sign * .43, -.015, .88))
        points = [shoulder.lerp(elbow, t) for t in (0, .18, .4, .66, .85, 1)] + [elbow.lerp(wrist, t) for t in (.18, .40, .65, .85, 1)]
        armw = lambda p, j, a=upper, b=fore, c=hand: blend_z(p.z, [(.88, c), (.92, b), (1.06, b), (1.14, a), (1.33, a)])
        skin.tube(points, [.050, .051, .046, .04, .033, .032, .036, .034, .029, .023, .021], skin_color, armw, 16, .95)
        sleevepts = [shoulder - (elbow - shoulder) * .12, shoulder, shoulder.lerp(elbow, .10), shoulder.lerp(elbow, .24), shoulder.lerp(elbow, .37)]
        sleevew = lambda p, j, bone=upper: {'chest': .5, bone: .5} if j == 0 else {bone: 1.0}
        cloth.tube(sleevepts, [.027, .051, .055, .055, .052], shirt_color, sleevew, 20, .96)
        p1, p2 = shoulder.lerp(elbow, .36), shoulder.lerp(elbow, .40)
        cloth.tube([p1, p2], [.053, .052], '4b2476', fixed(upper), 20, .96)
        # Palma e dedos em posição relaxada; deformação da mão por um osso.
        down = Vector((sign * .40, -.05, -.915)).normalized()
        palm_end = wrist + down * .075
        skin.tube([wrist, wrist + down * .023, wrist + down * .055, palm_end], [.021, .03, .03, .023], skin_color, fixed(hand), 12, .53)
        across = Vector((.915, 0, sign * .40))
        for fi, length in enumerate([.038, .050, .046, .035]):
            start = palm_end + across * ((fi - 1.5) * .013)
            end = start + down * (length * .20) + Vector((0, -.027, 0))
            mid = start + down * (length * .48) + Vector((0, -.004, 0))
            knuckle = start + down * (length * .58) + Vector((0, -.017, 0))
            skin.tube([start, mid, knuckle, end], [.007, .0065, .0055, .0035], skin_color, fixed(hand), 7, .80)
        thumb_base = wrist + down * .029 - sign * across * .023
        skin.tube([thumb_base, thumb_base + Vector((-sign * .017, -.005, -.015)), thumb_base + Vector((-sign * .020, -.014, -.038))], [.010, .009, .005], skin_color, fixed(hand), 8)

    # Pescoço e cabeça com queixo, mandíbula, maçãs e testa.
    skin.vertical([(1.345, 0, .004, .044, .037), (1.38, 0, .003, .041, .036), (1.435, 0, .003, .036, .035), (1.47, 0, -.002, .044, .039)], skin_color, lambda p, j: blend_z(p.z, [(1.35, 'chest'), (1.39, 'neck'), (1.46, 'head')]), 20)
    skin.vertical([
        (1.449, 0, -.026, .025, .028), (1.464, 0, -.018, .045, .042),
        (1.484, 0, -.003, .061, .052), (1.510, 0, .001, .070, .061),
        (1.542, 0, .002, .077, .067), (1.567, 0, .005, .075, .069),
        (1.590, 0, .009, .075, .072), (1.617, 0, .012, .073, .071),
        (1.643, 0, .014, .061, .062), (1.663, 0, .014, .040, .042),
        (1.671, 0, .014, .010, .014)
    ], skin_color, fixed('head'), 32)
    for sign in [-1, 1]:
        skin.ellipsoid((sign * .076, .009, 1.533), (.013, .018, .029), skin_color, fixed('head'), 12, 8)
        skin.ellipsoid((sign * .084, -.003, 1.534), (.005, .009, .017), '87523e', fixed('head'), 10, 6)
        # Olhos pequenos, sem proporção de personagem infantil.
        x, y, z = sign * .030, -.0615, 1.568
        skin.ellipsoid((x, y, z), (.014, .006, .006), 'd1bfae', fixed('head'), 16, 8)
        skin.ellipsoid((x, y - .0058, z), (.0050, .0018, .005), '48311f', fixed('head'), 12, 6)
        skin.ellipsoid((x, y - .0072, z), (.0023, .001, .0032), '151216', fixed('head'), 10, 6)
        lid = [(x + .015 * cos(a), y - .003 - .0015 * sin(a), z + .007 * sin(a)) for a in np.linspace(0, pi, 9)]
        skin.tube(lid, .0021, '875a43', fixed('head'), 6)
        brow = [(sign * .014, -.065, 1.583), (sign * .026, -.0635, 1.588), (sign * .039, -.0585, 1.587), (sign * .048, -.052, 1.582)]
        hair.tube(brow, [.002, .003, .0028, .0012], hair_color, fixed('head'), 6)
    skin.ellipsoid((0, -.066, 1.548), (.009, .012, .024), skin_color, fixed('head'), 14, 10)
    skin.ellipsoid((0, -.078, 1.531), (.012, .012, .009), 'aa7657', fixed('head'), 14, 8)
    for sign in [-1, 1]:
        skin.ellipsoid((sign * .01, -.073, 1.528), (.006, .008, .005), skin_color, fixed('head'), 10, 6)
        skin.ellipsoid((sign * .008, -.0785, 1.525), (.003, .003, .0016), '66402f', fixed('head'), 8, 4)
    skin.tube([(-.022, -.059, 1.506), (-.009, -.0645, 1.509), (0, -.066, 1.507), (.009, -.0645, 1.509), (.022, -.059, 1.506)], [.0015, .003, .003, .003, .0015], '885149', fixed('head'), 7)
    skin.tube([(-.02, -.059, 1.503), (0, -.0655, 1.501), (.02, -.059, 1.503)], [.0015, .0035, .0015], 'a56658', fixed('head'), 8)

    # Touca curva: linha frontal alta e cobertura da nuca, sem faixa calva atrás.
    skull_profile = [(1.51, .070, .061, .001), (1.542, .077, .067, .002),
        (1.567, .075, .069, .005), (1.59, .075, .072, .009),
        (1.617, .073, .071, .012), (1.643, .061, .062, .014),
        (1.663, .04, .042, .014), (1.676, .006, .009, .014),
        (1.683, .001, .001, .014)]
    def skull_at(z):
        for a, b in zip(skull_profile, skull_profile[1:]):
            if z <= b[0]:
                f = max(0, (z - a[0]) / (b[0] - a[0]))
                return [a[i] + f * (b[i] - a[i]) for i in (1, 2, 3)]
        return skull_profile[-1][1:]
    base = len(hair.verts)
    for j in range(7):
        t = j / 6
        for k in range(29):
            a = 2 * pi * k / 28
            back = (sin(a) + 1) / 2
            bottom_z = 1.612 - .081 * back
            z = bottom_z + (1.682 - bottom_z) * t
            rx, ry, cy = skull_at(z)
            p = Vector(((rx + .003) * cos(a), cy + (ry + .003) * sin(a), z))
            hair.vertex(p, (k / 28, t), hair_color, {'head': 1})
    for j in range(6):
        for k in range(28):
            a = base + j * 29 + k
            hair.faces.append((a, a + 1, a + 30, a + 29))
    # Tranças rentes ao couro cabeludo, da linha frontal para o alto da nuca.
    for b in range(8):
        x0 = (b - 3.5) * .017
        points = []
        for j in range(13):
            t = j / 12
            x = x0 * (1 - .63 * t)
            y = -.053 + .117 * t
            q = min(.985, (x / .082) ** 2 + ((y - .014) / .077) ** 2)
            z = 1.607 + .079 * math.sqrt(max(.015, 1 - q))
            points.append(Vector((x, y, z)))
        for strand in range(2):
            ps = [p + Vector((.0027 * sin(j * 2.2 + strand * pi), 0, .0027 * cos(j * 2.2 + strand * pi))) for j, p in enumerate(points)]
            hair.tube(ps, .0045, '2d211a' if strand else hair_color, fixed('head'), 5)

    def hair_weights(p, j):
        return blend_z(p.z, [(1.07, 'hair.03'), (1.25, 'hair.02'), (1.48, 'hair.01'), (1.65, 'hair.01')])

    # Oito tranças, cada uma com três cordões entrelaçados.
    for braid in range(8):
        a = 2 * pi * braid / 8
        for strand in range(3):
            points, radii = [], []
            for j in range(23):
                t = j / 22
                spread = .025 + .013 * sin(pi * t)
                center = Vector((spread * cos(a) + .014 * sin(t * 3.0), .071 + .084 * sin(t * pi * .78) + spread * sin(a), 1.658 - .58 * t + .017 * cos(a) * t))
                phase = t * 2 * pi * 6 + strand * 2 * pi / 3
                r = .0058 * (1 - .28 * t)
                center += Vector((r * cos(phase), r * sin(phase), 0))
                points.append(center)
                radii.append(.0072 * (1 - .40 * t))
            hair.tube(points, radii, ['251b16', '35271e', '1e1714'][strand], hair_weights, 5)
    # Elástico discreto no ponto de amarração.
    cloth.ellipsoid((0, .073, 1.642), (.034, .025, .014), '392148', fixed('head'), 16, 6)
    return [g.build(collection, rig) for g in (skin, cloth, hair)]


def point_at(obj, p):
    obj.rotation_euler = (Vector(p) - obj.location).to_track_quat('-Z', 'Y').to_euler()


def setup_studio(scene, collection):
    mat = bpy.data.materials.new('Studio_Chao')
    mat.diffuse_color = (.032, .041, .055, 1)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (.032, .041, .055, 1)
    bsdf.inputs['Roughness'].default_value = .88
    mesh = bpy.data.meshes.new('Studio_Chao')
    mesh.from_pydata([(-200, -200, -.012), (200, -200, -.012), (200, 200, -.012), (-200, 200, -.012)], [], [(0, 1, 2, 3)])
    floor = bpy.data.objects.new('Studio_Chao', mesh)
    collection.objects.link(floor)
    mesh.materials.append(mat)
    for name, loc, power, size, color in [
        ('Principal', (2, -3, 4), 330, 3.0, (1, .90, .79)),
        ('Preenchimento', (-2, -1.5, 2.4), 210, 2.4, (.75, .84, 1)),
        ('Recorte', (1, 2.2, 3.0), 450, 2.0, (.85, .87, 1)),
    ]:
        data = bpy.data.lights.new(name, 'AREA')
        data.energy, data.shape, data.size, data.color = power, 'DISK', size, color
        obj = bpy.data.objects.new(name, data)
        collection.objects.link(obj)
        obj.location = loc
        point_at(obj, (0, 0, .9))
    data = bpy.data.cameras.new('Camera_Apresentacao')
    cam = bpy.data.objects.new('Camera_Apresentacao', data)
    collection.objects.link(cam)
    data.type = 'ORTHO'
    data.ortho_scale = 1.98
    cam.location = (2.5, -4, 2.15)
    point_at(cam, (0, 0, .87))
    scene.camera = cam
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 24
    scene.cycles.use_denoising = True
    scene.render.resolution_x = 850
    scene.render.resolution_y = 1000
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    world = bpy.data.worlds.new('Studio_World')
    world.use_nodes = True
    world.node_tree.nodes['Background'].inputs[0].default_value = (.14, .17, .22, 1)
    world.node_tree.nodes['Background'].inputs[1].default_value = .4
    scene.world = world
    scene.view_settings.view_transform = 'AgX'
    return cam


def select_action(rig, action):
    rig.animation_data_create()
    for track in rig.animation_data.nla_tracks:
        track.mute = True
    rig.animation_data.action = action
    if hasattr(action, 'slots') and len(action.slots):
        rig.animation_data.action_slot = action.slots[0]


def resolve_output():
    global RENDER_PREVIEWS
    selected = OUTPUT_DIR
    if '--' in sys.argv:
        parser = argparse.ArgumentParser()
        parser.add_argument('--output', default='')
        parser.add_argument('--no-render', action='store_true')
        opts = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
        selected = opts.output or selected
        RENDER_PREVIEWS = not opts.no_render
    if not selected:
        try:
            base = Path(__file__).resolve().parent
        except NameError:
            text = getattr(bpy.context.space_data, 'text', None)
            if text and text.filepath:
                base = Path(bpy.path.abspath(text.filepath)).resolve().parent
            elif bpy.data.filepath:
                base = Path(bpy.data.filepath).parent
            else:
                base = Path(bpy.app.tempdir)
        selected = base / 'corre_pro_ponto_personagem'
    out = Path(selected).expanduser().resolve()
    if out.exists() and any(out.iterdir()):
        out = out.with_name(out.name + '_' + datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    out.mkdir(parents=True, exist_ok=True)
    return out


def export_asset(scene, rig, meshes, actions, out):
    scene.frame_set(1)
    rig.data.pose_position = 'POSE'
    for obj in bpy.context.view_layer.objects:
        obj.select_set(False)
    for obj in [rig, *meshes]:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = rig
    props = {p.identifier for p in bpy.ops.export_scene.gltf.get_rna_type().properties}
    options = dict(filepath=str(out / 'personagem_runner.glb'), export_format='GLB',
        use_selection=True, use_active_scene=True, export_yup=True, export_animations=True,
        export_animation_mode='ACTIONS', export_force_sampling=True,
        export_anim_single_armature=False,
        export_skins=True, export_def_bones=False, export_materials='EXPORT',
        export_rest_position_armature=True, export_reset_pose_bones=True,
        export_cameras=False, export_lights=False, export_apply=False,
        export_all_influences=False, export_vertex_color='NAME',
        export_vertex_color_name='Color', export_all_vertex_colors=False)
    bpy.ops.export_scene.gltf(**{k: v for k, v in options.items() if k in props})
    rig.data.pose_position = 'POSE'


def run():
    out = resolve_output()
    # Uma nova cena evita apagar ou alterar os objetos da cena do usuário.
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    scene = bpy.data.scenes.new('Personagem_Runner')
    bpy.context.window.scene = scene
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.scale_length = 1.0
    scene.render.fps = 30
    character = bpy.data.collections.new('PERSONAGEM_EXPORTAR')
    studio = bpy.data.collections.new('STUDIO_NAO_EXPORTAR')
    scene.collection.children.link(character)
    scene.collection.children.link(studio)
    rig = create_rig(character)
    meshes = make_character(character, rig)
    actions = create_animations(rig)
    print('ACTIONS', list(actions))
    select_action(rig, actions['run_loop'])
    # NLA muted e ações marcadas Fake User; exporter em modo ACTIONS preserva clipes.
    export_asset(scene, rig, meshes, actions, out)
    cam = setup_studio(scene, studio)
    stats = {'blender_version': bpy.app.version_string, 'triangles': 0,
        'vertices': 0, 'materials': 3, 'bones': len(rig.data.bones),
        'animations': list(actions), 'texture_size': TEXTURE_SIZE,
        'style': 'base procedural semi-realista, sem escultura manual',
        'forward_blender': '-Y', 'forward_godot': '+Z',
        'godot_tested': False, 'android_tested': False,
        'root_motion': 'runtime clips in-place; *_motion contain preview displacement',
        'run_reference_speed_m_s': rig.get('run_reference_speed_m_s', 2.06)}
    for obj in meshes:
        obj.data.calc_loop_triangles()
        stats['triangles'] += len(obj.data.loop_triangles)
        stats['vertices'] += len(obj.data.vertices)
    if stats['triangles'] > 20000:
        print('AVISO: modelo excede orçamento inicial de 20000 triângulos.')
    (out / 'informacoes_modelo.json').write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding='utf-8')
    manifest = {'project': 'Corre pro Ponto', 'target_godot': '4.7.2',
        'run_speed_m_s': RUN_SPEED, 'lane_width_m': LANE_WIDTH, 'lane_seconds': LANE_SECONDS,
        'gravity_m_s2': GRAVITY, 'hair_solver': 'PBD 120 Hz: gravity, inertia, drag, body collision proxies',
        'runtime_hair': 'Godot SpringBoneSimulator3D; disable baked hair tracks',
        'clips': {name: {'seconds': frames/FPS, 'loop': loop, 'root_motion': root_mode}
                  for name, frames, maker, loop, shift, root_mode in animation_specs()}}
    (out / 'animacoes.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    demo_action = create_demo_sequence(rig, actions, scene)
    select_action(rig, demo_action)
    scene.frame_set(7)
    cam.location = (1.8, 4.3, 2.1)
    point_at(cam, (0, 0, .83))
    # Vista pronta para reproduzir a animação ao abrir o .blend.
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                area.spaces.active.region_3d.view_distance = 2.7
                area.spaces.active.region_3d.view_location = (0, 0, .9)
                area.spaces.active.shading.type = 'MATERIAL'
    for obj in bpy.context.view_layer.objects:
        obj.select_set(False)
    rig.select_set(True)
    bpy.context.view_layer.objects.active = rig
    # Salva o asset antes dos renders: uma interrupção na prévia não perde o .blend.
    bpy.ops.wm.save_as_mainfile(filepath=str(out / 'personagem_runner.blend'))
    if RENDER_PREVIEWS:
        try:
            select_action(rig, actions['idle'])
            scene.frame_set(1)
            cam.location = (2.1, -4, 2.0)
            point_at(cam, (0, 0, .87))
            scene.render.filepath = str(out / 'previa_frente.png')
            bpy.ops.render.render(write_still=True)
            select_action(rig, actions['run_loop'])
            scene.frame_set(7)
            cam.location = (1.8, 4.3, 2.1)
            point_at(cam, (0, 0, .83))
            scene.render.filepath = str(out / 'previa_corrida.png')
            bpy.ops.render.render(write_still=True)
        finally:
            select_action(rig, demo_action)
            scene.frame_set(7)
            cam.location = (1.8, 4.3, 2.1)
            point_at(cam, (0, 0, .83))
    print('RUNNER_OUTPUT=' + str(out))
    print('RUNNER_STATS=' + json.dumps(stats))


# As funções do rig e das animações são incorporadas acima deste módulo na entrega.
if __name__ == '__main__':
    run()
