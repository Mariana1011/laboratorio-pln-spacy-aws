from flask import Flask, request, jsonify, Response
import spacy
from spacy import displacy

import math
import unicodedata
from collections import Counter


app = Flask(__name__)

# Permite devolver correctamente tildes y ñ
app.json.ensure_ascii = False


# =========================================================
# MODELO DE SPACY
# =========================================================

# Modelo exigido por el profesor
nlp = spacy.load("es_core_news_sm")


# =========================================================
# FUNCIONES AUXILIARES
# =========================================================

def error_response(message, status=400):
    """
    Genera respuestas de error controladas.
    """

    return jsonify({
        "error": message
    }), status


def get_json_body():
    """
    Verifica que la solicitud utilice application/json
    y que el cuerpo sea un objeto JSON válido.
    """

    if request.mimetype != "application/json":
        return None, error_response(
            "Content-Type debe ser application/json",
            415
        )

    data = request.get_json(silent=True)

    if data is None:
        return None, error_response(
            "El cuerpo JSON es inválido",
            400
        )

    if not isinstance(data, dict):
        return None, error_response(
            "El cuerpo JSON debe ser un objeto",
            400
        )

    return data, None


def validar_texto_o_batch(data):
    """
    Para:
    /clean
    /pos
    /ner

    Acepta:
    - un string
    - una lista de strings

    Siempre devuelve internamente una lista.
    """

    if "text" not in data:
        return None, error_response(
            "Falta el campo obligatorio 'text'",
            400
        )

    value = data["text"]

    # -------------------------
    # Texto individual
    # -------------------------

    if isinstance(value, str):

        if not value.strip():
            return None, error_response(
                "'text' no puede estar vacío",
                400
            )

        return [value], None

    # -------------------------
    # Batch
    # -------------------------

    if isinstance(value, list):

        if len(value) == 0:
            return None, error_response(
                "'text' no puede ser una lista vacía",
                400
            )

        # IMPORTANTE:
        # se valida TODO antes de procesar
        for item in value:

            if not isinstance(item, str):
                return None, error_response(
                    "Todos los elementos de 'text' deben ser strings",
                    400
                )

            if not item.strip():
                return None, error_response(
                    "Los elementos de 'text' no pueden estar vacíos",
                    400
                )

        return value, None

    return None, error_response(
        "'text' debe ser un string o una lista de strings",
        400
    )


def validar_texto_individual(data):
    """
    Validación exclusiva para dependencias.
    No permite batch.
    """

    if "text" not in data:
        return None, error_response(
            "Falta el campo obligatorio 'text'",
            400
        )

    text = data["text"]

    if not isinstance(text, str):
        return None, error_response(
            "'text' debe ser un único string",
            400
        )

    if not text.strip():
        return None, error_response(
            "'text' no puede estar vacío",
            400
        )

    return text, None


def validar_documentos(data):
    """
    Validación de vectorización.

    Requiere:
    documents = lista con mínimo 2 strings.
    """

    if "documents" not in data:
        return None, error_response(
            "Falta el campo obligatorio 'documents'",
            400
        )

    documents = data["documents"]

    if not isinstance(documents, list):
        return None, error_response(
            "'documents' debe ser una lista",
            400
        )

    if len(documents) < 2:
        return None, error_response(
            "'documents' debe contener al menos dos documentos",
            400
        )

    # Validamos TODO el lote antes de procesarlo
    for document in documents:

        if not isinstance(document, str):
            return None, error_response(
                "Todos los elementos de 'documents' deben ser strings",
                400
            )

        if not document.strip():
            return None, error_response(
                "Los documentos no pueden estar vacíos",
                400
            )

    return documents, None


# =========================================================
# LIMPIEZA
# =========================================================

def reemplazar_puntuacion_por_espacios(text):
    """
    La puntuación debe actuar como separador.

    Ejemplo:
    hola,mundo
    pasa a:
    hola mundo

    y no a:
    holamundo
    """

    return "".join(
        " " if unicodedata.category(char).startswith("P") else char
        for char in text
    )


def limpiar_textos(texts):
    """
    Reglas del profesor:

    1. pasar a minúsculas
    2. eliminar signos de puntuación
    3. eliminar stopwords según Token.is_stop
    4. normalizar espacios
    5. conservar tildes, ñ y números
    """

    preparados = [
        reemplazar_puntuacion_por_espacios(text).lower()
        for text in texts
    ]

    resultados = []

    for doc in nlp.pipe(preparados):

        palabras = [
            token.text
            for token in doc
            if not token.is_space
            and not token.is_punct
            and not token.is_stop
        ]

        texto_limpio = " ".join(palabras)

        resultados.append(texto_limpio)

    return resultados


# =========================================================
# POS
# =========================================================

def analizar_pos(texts):
    """
    Devuelve:
    - text
    - pos
    - lemma
    """

    results = []

    for doc in nlp.pipe(texts):

        tokens = []

        for token in doc:

            if not token.is_space:

                tokens.append({
                    "text": token.text,
                    "pos": token.pos_,
                    "lemma": token.lemma_
                })

        results.append({
            "tokens": tokens
        })

    return results


# =========================================================
# NER
# =========================================================

def analizar_ner(texts):
    """
    Devuelve entidades usando las posiciones
    del TEXTO ORIGINAL.

    start: inclusivo
    end: exclusivo
    """

    results = []

    for doc in nlp.pipe(texts):

        entities = []

        for ent in doc.ents:

            entities.append({
                "text": ent.text,
                "label": ent.label_,
                "start": ent.start_char,
                "end": ent.end_char
            })

        results.append({
            "entities": entities
        })

    return results


# =========================================================
# DEPENDENCIAS
# =========================================================

def visualizar_dependencias(text):
    """
    Genera HTML que contiene un SVG mediante displaCy.
    """

    doc = nlp(text)

    html = displacy.render(
        doc,
        style="dep",
        page=True,
        jupyter=False
    )

    return html


# =========================================================
# VECTORIZACIÓN
# =========================================================

def vectorizar(documentos):

    # Primero se aplica EXACTAMENTE la misma limpieza
    documentos_limpios = limpiar_textos(documentos)

    documentos_tokenizados = [
        texto.split() if texto else []
        for texto in documentos_limpios
    ]

    # =====================================================
    # VOCABULARIO
    # =====================================================

    # Debe estar en orden lexicográfico ascendente
    vocabulary = sorted({
        palabra
        for documento in documentos_tokenizados
        for palabra in documento
    })

    indice_vocabulario = {
        palabra: indice
        for indice, palabra in enumerate(vocabulary)
    }

    tam_vocabulario = len(vocabulary)

    # =====================================================
    # BAG OF WORDS
    # =====================================================

    bag_of_words = []

    for documento in documentos_tokenizados:

        conteo = Counter(documento)

        fila = [
            conteo.get(palabra, 0)
            for palabra in vocabulary
        ]

        bag_of_words.append(fila)

    # =====================================================
    # ONE-HOT
    # =====================================================

    # Cada OCURRENCIA genera una fila.
    one_hot = []

    for documento in documentos_tokenizados:

        matriz_documento = []

        for palabra in documento:

            vector = [0] * tam_vocabulario

            vector[
                indice_vocabulario[palabra]
            ] = 1

            matriz_documento.append(vector)

        one_hot.append(matriz_documento)

    # =====================================================
    # TF-IDF
    # =====================================================

    numero_documentos = len(documentos_tokenizados)

    idf = {}

    for palabra in vocabulary:

        nt = sum(
            1
            for documento in documentos_tokenizados
            if palabra in documento
        )

        idf[palabra] = (
            math.log(
                (numero_documentos + 1)
                /
                (nt + 1)
            )
            + 1
        )

    tf_idf = []

    for documento in documentos_tokenizados:

        conteo = Counter(documento)

        fila = []

        for palabra in vocabulary:

            tf = conteo.get(palabra, 0)

            valor = tf * idf[palabra]

            fila.append(
                round(valor, 4)
            )

        tf_idf.append(fila)

    return {
        "vocabulary": vocabulary,
        "one_hot": one_hot,
        "bag_of_words": bag_of_words,
        "tf_idf": tf_idf
    }


# =========================================================
# RUTA AUXILIAR
# =========================================================

@app.route("/", methods=["GET"])
def inicio():

    return jsonify({
        "message": "API de PLN funcionando"
    })


@app.route("/health", methods=["GET"])
def health():

    return jsonify({
        "status": "ok"
    })


# =========================================================
# 1. CLEAN
# =========================================================

@app.route("/api/v1/clean", methods=["POST"])
def clean():

    data, error = get_json_body()

    if error:
        return error

    texts, error = validar_texto_o_batch(data)

    if error:
        return error

    resultados = limpiar_textos(texts)

    return jsonify({
        "cleaned_text": resultados
    })


# =========================================================
# 2. POS
# =========================================================

@app.route("/api/v1/pos", methods=["POST"])
def pos():

    data, error = get_json_body()

    if error:
        return error

    texts, error = validar_texto_o_batch(data)

    if error:
        return error

    results = analizar_pos(texts)

    return jsonify({
        "results": results
    })


# =========================================================
# 3. NER
# =========================================================

@app.route("/api/v1/ner", methods=["POST"])
def ner():

    data, error = get_json_body()

    if error:
        return error

    texts, error = validar_texto_o_batch(data)

    if error:
        return error

    results = analizar_ner(texts)

    return jsonify({
        "results": results
    })


# =========================================================
# 4. VISUALIZACIÓN DE DEPENDENCIAS
# =========================================================

@app.route(
    "/api/v1/visualize/dep",
    methods=["POST"]
)
def dependency():

    data, error = get_json_body()

    if error:
        return error

    text, error = validar_texto_individual(data)

    if error:
        return error

    html = visualizar_dependencias(text)

    return Response(
        html,
        status=200,
        content_type="text/html; charset=utf-8"
    )


# =========================================================
# 5. VECTORIZACIÓN
# =========================================================

@app.route("/api/v1/vectorize", methods=["POST"])
def vectorize():

    data, error = get_json_body()

    if error:
        return error

    documentos, error = validar_documentos(data)

    if error:
        return error

    resultados = vectorizar(documentos)

    return jsonify(resultados)


# =========================================================
# EJECUCIÓN
# =========================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=8080,
        threaded=True,
        debug=False
    )
