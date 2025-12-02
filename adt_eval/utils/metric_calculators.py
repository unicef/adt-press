from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer('sentence-transformers/LaBSE')

def labse_score_calculator(original_text, translated_text):
    try:
        emb1 = model.encode(original_text, convert_to_tensor=True, show_progress_bar=False)
        emb2 = model.encode(translated_text, convert_to_tensor=True, show_progress_bar=False)
        return util.pytorch_cos_sim(emb1, emb2).item()
    except Exception as exc:
        logging.error(f"LaBSE error: {exc}")
        return 0.0
