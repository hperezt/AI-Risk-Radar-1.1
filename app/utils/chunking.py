# app/utils/chunking.py

# Importamos la librería oficial para contar tokens como GPT-4o los cuenta
import tiktoken

# Función que cuenta cuántos tokens hay en un texto, usando el modelo especificado
def count_tokens(text: str, model: str = "gpt-4o") -> int:
    encoding = tiktoken.encoding_for_model(model)  # Usa el esquema de tokenización del modelo
    return len(encoding.encode(text))              # Devuelve la cantidad de tokens

# Función que divide el texto largo en chunks basados en un máximo de tokens permitidos
def split_into_chunks(text: str, max_tokens: int = 3000, model: str = "gpt-4o") -> list:
    paragraphs = text.split("\n\n")  # Divide por párrafos usando saltos dobles de línea
    chunks = []                      # Lista para guardar los bloques finales
    current_chunk = ""              # Acumulador temporal

    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            continue  # Salta párrafos vacíos

        # Simula agregar el párrafo al bloque actual
        test_chunk = current_chunk + "\n\n" + paragraph if current_chunk else paragraph

        # Si el bloque no supera el límite de tokens, lo agregamos al chunk actual
        if count_tokens(test_chunk, model) <= max_tokens:
            current_chunk = test_chunk
        else:
            # Si supera el límite, guardamos el chunk actual y evaluamos el nuevo párrafo por separado
            if current_chunk:
                chunks.append(current_chunk.strip())

            # Si el párrafo solo ya es demasiado largo, lo troceamos por oraciones
            if count_tokens(paragraph, model) > max_tokens:
                sentences = paragraph.split(". ")  # Rompe en oraciones simples
                temp = ""
                for s in sentences:
                    s = s.strip()
                    test = temp + ". " + s if temp else s
                    if count_tokens(test, model) <= max_tokens:
                        temp = test
                    else:
                        if temp:
                            chunks.append(temp.strip())
                        temp = s
                if temp:
                    chunks.append(temp.strip())
                current_chunk = ""
            else:
                # Si el párrafo entra bien solo, lo usamos como nuevo chunk
                current_chunk = paragraph

    # Agrega el último chunk si quedó algo sin cerrar
    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks
