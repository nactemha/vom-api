from fastapi import FastAPI, HTTPException, Query, Response
from pydantic import BaseModel
from TTS.api import TTS
from text_norm import text_normalize
from multiprocessing import Lock
import time
import io
import os
from typing import List
from cachetools import cached, TTLCache
import json
import time
from typing import Optional



app = FastAPI()

lock = Lock()
active_models = {}

MODEL_FOLDER_PATH = os.environ.get("MODEL_FOLDER_PATH", "models")

# Create a TTLCache for actor models. Cache will expire in 5 minutes.
cache = TTLCache(maxsize=100, ttl=600)

class TTSRequest(BaseModel):
    actor: str
    text: str


class ActorModel(BaseModel):
    actorId: str
    actorName: str
    actorDescription: Optional[str] = None
    actorGender: str
    actorAge: Optional[str] = None
    actorLanguage: str
    actorCountry: str
    ttsModel: str
    vocoderModel: Optional[str] = None
    


MODEL_FOLDER_PATH = os.environ.get("MODEL_FOLDER_PATH", "models")

def create_model(ttsmodel, vocodermodel):
    if vocodermodel is not None:
        return TTS(model_path=f"{MODEL_FOLDER_PATH}/{ttsmodel}/model.pth",
                   config_path=f"{MODEL_FOLDER_PATH}/{ttsmodel}/config.json",
                   vocoder_path=f"{MODEL_FOLDER_PATH}/{vocodermodel}/model.pth",
                   vocoder_config_path=f"{MODEL_FOLDER_PATH}/{vocodermodel}/config.json",
                   progress_bar=False, gpu=False)
    else:
        return TTS(model_path=f"{MODEL_FOLDER_PATH}/{ttsmodel}/model.pth",
                   config_path=f"{MODEL_FOLDER_PATH}/{ttsmodel}/config.json",
                   progress_bar=False, gpu=False)

def clean_unused_models():
    for modelid in list(active_models.keys()):
        model = active_models[modelid]
        if time.time() - model["lastused"] > 60 * 60:
            del active_models[modelid]


def get_model(ttsmodel, vocodermodel):
    with lock:
        if ttsmodel not in active_models:
            active_models[ttsmodel] = {
                "model": create_model(ttsmodel, vocodermodel),
                "lastused": time.time(),
                "lock": Lock()
            }
        model = active_models[ttsmodel]
        model["lastused"] = time.time()
        clean_unused_models()
        return model["model"], model["lock"]


@cached(cache)
def get_actor_models():
    json_file_path = MODEL_FOLDER_PATH + "/actors.json"
    with open(json_file_path, "r") as f:
        actors = json.load(f)
    return actors

@app.get("/api/reset")
def reset():
    with lock:
        active_models.clear()
    cache.clear()
    return "OK"

@app.get("/api/actors", response_model=List[ActorModel])
async def get_actors():
    actors = get_actor_models()
    return actors

@app.post("/api/tts")
async def post_tts(request: TTSRequest):
    try:
        actor = request.actor.lower()
        # Assuming get_actor_models returns a list of actor dictionaries
        actors = get_actor_models()
        actor_model = next((item for item in actors if item["actorId"] == actor), None)
        print(actor_model)

        if actor_model is None:
            raise HTTPException(status_code=400, detail="Invalid actor.")
        ttsmodel=actor_model.get("ttsModel", "")
        vocodermodel=actor_model.get("vocoderModel", None)
        language=actor_model.get("actorLanguage", "")
        if ttsmodel == "":
            raise HTTPException(status_code=400, detail="Invalid actor.")
        if language == "":
            raise HTTPException(status_code=400, detail="Invalid actor.")
        if vocodermodel == "":
            vocodermodel = None
        

        text = text_normalize(request.text, language)
        tts, lock = get_model(ttsmodel, vocodermodel)

        with lock:
            ttsaudio = tts.tts(text)
            wav_data = io.BytesIO()
            tts.synthesizer.save_wav(ttsaudio, wav_data)
            wav_data = wav_data.getvalue()

        return Response(content=wav_data, media_type="audio/wav")



    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    HTTP_PORT = os.environ.get("HTTP_PORT", 8000)
    uvicorn.run(app, host="0.0.0.0", port=int(HTTP_PORT))