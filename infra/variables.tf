variable "proyecto" {
  description = "Identificador del proyecto para etiquetar recursos"
  type        = string
  default     = "nebula-arena"
}

variable "region" {
  description = "Región de AWS donde se desplegará Nebula Arena"
  type        = string
  default     = "us-east-1"
}

variable "nodos_juego" {
  description = "Nodos iniciales del pool de servidores de juego en EKS"
  type        = number
  default     = 3
}

variable "min_nodos" {
  description = "Mínimo de nodos en el Managed Node Group de EKS"
  type        = number
  default     = 3
}

variable "max_nodos" {
  description = "Máximo de nodos en el Managed Node Group de EKS"
  type        = number
  default     = 20
}

variable "tipo_instancia" {
  description = "Instancia optimizada a cómputo para servidores de partida"
  type        = string
  default     = "c7i.xlarge"
}
