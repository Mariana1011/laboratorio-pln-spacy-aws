# Laboratorio I - Procesamiento de texto con spaCy y AWS

## Descripción

Este proyecto implementa un microservicio de Procesamiento de Lenguaje Natural utilizando **Python, Flask y spaCy**, con el modelo de español `es_core_news_sm`.

La solución fue desplegada en dos arquitecturas de AWS:

1. **EC2 asociada al entorno AWS Academy/Cloud9**
2. **AWS Lambda con Function URL pública**

Ambos despliegues utilizan la misma lógica funcional y ofrecen los mismos endpoints.

---

## Funcionalidades

La API implementa las siguientes capacidades:

* Limpieza de texto.
* Análisis POS y lematización.
* Reconocimiento de entidades nombradas (NER).
* Visualización de dependencias mediante displaCy.
* Vectorización mediante:

  * One-Hot
  * Bag of Words
  * TF-IDF

También soporta procesamiento por lotes, validación de entradas y respuestas HTTP 4xx controladas.

---

## Endpoints

### Limpieza

```text
POST /api/v1/clean
```

Entrada:

```json
{
  "text": "El niño estudia en Bogotá."
}
```

También acepta una lista de strings.

---

### POS y lematización

```text
POST /api/v1/pos
```

Entrada:

```json
{
  "text": "María estudia ingeniería."
}
```

---

### Reconocimiento de entidades

```text
POST /api/v1/ner
```

Entrada:

```json
{
  "text": "María vive en Bogotá y trabaja en Microsoft."
}
```

---

### Dependencias sintácticas

```text
POST /api/v1/visualize/dep
```

Entrada:

```json
{
  "text": "María estudia procesamiento de lenguaje natural."
}
```

La respuesta es un documento HTML que contiene un SVG generado mediante spaCy displaCy.

---

### Vectorización

```text
POST /api/v1/vectorize
```

Entrada:

```json
{
  "documents": [
    "Gato, gato y pescado.",
    "Gato come rápido."
  ]
}
```

La respuesta contiene:

* `vocabulary`
* `one_hot`
* `bag_of_words`
* `tf_idf`

---

## URLs de despliegue

### EC2 / Cloud9

```text
http://34.204.240.213:8080
```

El despliegue EC2 utiliza la Elastic IP `34.204.240.213`, por lo que la URL pública del servicio es estable mientras la Elastic IP permanezca asociada a la instancia.

### AWS Lambda

```text
https://4eeqcolhvmxws7gjbgf4bjagom0jbqer.lambda-url.us-east-1.on.aws/
```

---

## Ejecución en EC2

El proyecto utiliza un servicio `systemd` llamado:

```text
pln-api.service
```

Para comprobar su estado:

```bash
sudo systemctl status pln-api
```

Para reiniciarlo:

```bash
sudo systemctl restart pln-api
```

La aplicación utiliza Gunicorn y escucha en:

```text
0.0.0.0:8080
```

---

## Tecnologías utilizadas

* Python
* Flask
* spaCy
* `es_core_news_sm`
* Gunicorn
* AWS EC2
* AWS Cloud9
* AWS Lambda
* AWS Lambda Function URL
* Amazon S3

---

## Validaciones implementadas

La API rechaza mediante respuestas HTTP 4xx:

* Campos obligatorios ausentes.
* Valores `null`.
* Tipos incorrectos.
* Listas vacías.
* Elementos no string.
* Textos vacíos o compuestos solo por espacios.
* Procesamiento batch en `/api/v1/visualize/dep`.
* Menos de dos documentos en `/api/v1/vectorize`.

Si un lote contiene un elemento inválido, se rechaza la solicitud completa.

---

## Pruebas realizadas

Se verificó:

* Funcionamiento de los cinco endpoints.
* Procesamiento batch.
* 25 documentos en limpieza.
* Cinco solicitudes concurrentes.
* Respuestas HTTP 400 ante entradas inválidas.
* Generación de SVG mediante displaCy.
* Paridad funcional entre EC2 y Lambda.
* Coincidencia de resultados en:

  * limpieza,
  * POS,
  * NER,
  * vectorización.

---

## Uso de inteligencia artificial generativa

Durante el desarrollo del laboratorio se utilizó **ChatGPT de OpenAI** como herramienta de apoyo.

Se utilizó para:

* interpretar los requisitos del laboratorio;
* apoyar la implementación de la API;
* revisar validaciones;
* preparar casos de prueba;
* apoyar la configuración de los despliegues en EC2 y AWS Lambda;
* diagnosticar errores encontrados durante las pruebas.

Todo código y recomendación incorporados al proyecto fueron verificados mediante ejecución directa en AWS.

Se realizaron pruebas funcionales, pruebas de entradas inválidas, procesamiento por lotes, concurrencia y comparación de resultados entre EC2 y Lambda.

No se compartieron con la herramienta contraseñas, claves secretas, tokens, credenciales de AWS Academy ni otra información sensible.

---

## Estructura recomendada del repositorio

```text
pln-laboratorio/
│
├── common/
│   └── app.py
│
├── ec2/
│   └── pln-api.service
│
├── lambda/
│   └── lambda_function.py
│
├── requirements.txt
└── README.md
```

La lógica funcional se mantiene común para ambos despliegues y los archivos específicos de infraestructura se encuentran separados por arquitectura.

