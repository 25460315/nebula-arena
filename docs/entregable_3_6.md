# Entregable 3.6 — Infraestructura como Código con Terraform en AWS

**Proyecto:** Nebula Arena  
**Región:** `us-east-1` | **Cuenta AWS:** `131470772842`  
**Backend Remoto:** `s3://nebula-tfstate-131470772842/dev/terraform.tfstate` + bloqueo DynamoDB `nebula-tfstate-lock`

---

## 1. Estructura del Directorio `infra/`

```text
infra/
├── main.tf        # Providers AWS/Helm y backend remoto S3 + DynamoDB state locking
├── variables.tf   # Variables proyecto ("nebula"), region ("us-east-1") y nodos_juego (3)
├── red.tf         # Módulo oficial VPC (10.0.0.0/16) y Security Group TCP/UDP 7000-8000
├── eks.tf         # Módulo oficial EKS (nebula-default, pool c7i.xlarge 3..20) y repo ECR
├── agones.tf      # Release Helm de Agones autenticado contra el endpoint de EKS
└── outputs.tf     # Outputs: nombre del clúster EKS y URL del repositorio ECR
```

---

## 2. Guía de Evidencias y Capturas Obligatorias

### Captura 1 — Revisión de `terraform plan` (y validación en Pull Request)
1. Ejecutar en `infra/`:
   ```bash
   terraform init
   terraform fmt -check
   terraform validate
   terraform plan -out plan.tfplan
   ```
2. **Para la captura del Pull Request:**
   - Crear una rama (`git checkout -b feat/infra-terraform`), hacer commit de la carpeta `infra/` y abrir un Pull Request hacia `main` en GitHub (`25460315/nebula-arena`), pegando en la descripción del PR el resumen de `terraform plan` (`Plan: XX to add, 0 to change, 0 to destroy`).

### Captura 2 — Clúster `nebula-default` y Agones Activos tras `terraform apply`
1. Ejecutar:
   ```bash
   terraform apply plan.tfplan
   aws eks update-kubeconfig --name nebula-default --region us-east-1
   kubectl get nodes
   kubectl get pods -n agones-system
   ```
2. Tomar captura de la salida de `Apply complete! Resources: XX added, 0 changed, 0 destroyed` mostrando los `Outputs: cluster = "nebula-default"` y `registro = "131470772842.dkr.ecr.us-east-1.amazonaws.com/nebula-server"`, junto con `kubectl get nodes` y los pods de `agones-system` corriendo.

### Captura 3 — Destrucción Total (`terraform destroy`) sin Recursos Huérfanos Cobrando
1. Al finalizar la sesión de laboratorio, eliminar primero los objetos Kubernetes que crean LoadBalancers externos (para que no bloqueen el borrado de la VPC) y luego ejecutar `terraform destroy`:
   ```bash
   kubectl delete -f ../k8s/ --ignore-not-found
   terraform destroy -auto-approve
   ```
2. Tomar captura del mensaje final:
   - `Destroy complete! Resources: XX destroyed.`
   - Verificación en consola/CLI (`aws eks list-clusters --region us-east-1` y `aws ec2 describe-instances --filters "Name=instance-state-name,Values=running" --region us-east-1`) demostrando **0 clústeres y 0 instancias EC2 encendidas**.
