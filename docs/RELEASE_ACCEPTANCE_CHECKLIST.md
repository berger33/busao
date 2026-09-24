# Checklist de aceite gráfico e performance

## Gates estáticos

- [x] GLB da heroína válido
- [x] Partes mesh-only validadas
- [x] Auditoria de materiais de asfalto/calçada
- [x] Manifesto de assets gerado
- [x] Gate de LOD implementado
- [x] Auditoria de geometria runtime
- [x] Telemetria de performance
- [x] Overlay de QA opt-in

## Gates ainda bloqueados

- [ ] Heroína rigged
- [ ] Clips Idle/Walk/Sprint/Jump/Crouch
- [ ] LOD0/LOD1/LOD2 para assets P0/P1
- [ ] Captura Godot no perfil Mobile
- [ ] Captura Godot no perfil Compatibility
- [ ] Teste em Android mínimo
- [ ] Teste em Android recomendado
- [ ] FPS médio mínimo de 30
- [ ] FPS recomendado de 60
- [ ] Memória e draw calls dentro do orçamento
- [ ] Validação visual final sem clipping/gaps/T-pose

## Critério de release

Não marcar o projeto como 10/10 enquanto qualquer item de “Gates ainda bloqueados” estiver aberto. O overlay deve ser executado com `BUSAO_PERF=1` durante a corrida, e os resultados devem ser anexados ao relatório de QA antes do aceite.

## Próximo passo executável

Produzir os LODs reais e o rig da heroína. Depois executar o jogo em Godot com o overlay e preencher as métricas de FPS/frame time por aparelho.
