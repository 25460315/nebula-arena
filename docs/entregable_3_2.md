# Entregable 3.2 — Pipeline CI/CD con GitHub Actions y Amazon ECR

## 1. Guía de Capturas de Evidencia

1. **Captura 1 — Pipeline en verde en GitHub Actions:**
   - Pestaña **Actions** del repositorio `25460315/nebula-arena` mostrando el workflow `nebula-server-ci` completado con éxito (`✓ build`), desglosando los pasos `Pruebas`, `Configurar credenciales AWS (OIDC)`, `Login en Amazon ECR` y `Construir y publicar imagen`.
2. **Captura 2 — Imagen publicada en Amazon ECR con etiqueta `<SHA>`:**
   - Consola de **Amazon ECR -> Repositories -> `nebula-server`** (o salida de `aws ecr describe-images --repository-name nebula-server --region us-east-1`) mostrando la imagen recién publicada con el `imageTag` igual al SHA de 40 caracteres del commit de GitHub.
3. **Captura 3 — Actualización y drenado de partidas en Agones:**
   - Salida de `kubectl get gameservers -w` tras aplicar `k8s/fleet.yaml` con el nuevo `<SHA>`, donde se observa que los servidores en estado `Ready` se reemplazan inmediatamente por pods con la nueva imagen, mientras que el servidor en estado `Allocated` permanece intacto hasta finalizar su partida.

---

## 2. Explicación Técnica: ¿Cómo hacer *Rollback* a la versión anterior?

Dado que cada ejecución del pipeline CI/CD genera una imagen Docker inmutable en Amazon ECR etiquetada con el hash único del commit (`131470772842.dkr.ecr.us-east-1.amazonaws.com/nebula-server:<SHA>`), hacer *rollback* no requiere recompilar código ni reconstruir contenedores: basta con cambiar la etiqueta de la imagen en `k8s/fleet.yaml` apuntando al `<SHA_ANTERIOR>` (o a `:1.0`) mediante `sed -i "s|nebula-server:.*|nebula-server:<SHA_ANTERIOR>|" k8s/fleet.yaml` (o `git revert` en GitOps) y ejecutar `kubectl apply -f k8s/fleet.yaml`. Al aplicar el manifiesto, Agones ejecuta una actualización progresiva con **drenado de partidas (*game-specific draining*)**: reemplaza al instante todos los `GameServers` en estado `Ready` por contenedores con la versión anterior estable, de modo que cualquier partida nueva se asigne ya a la versión revertida, mientras que los pods que estaban en estado `Allocated` no se interrumpen y se eliminan únicamente cuando sus jugadores terminan la partida e invocan `/shutdown`.
