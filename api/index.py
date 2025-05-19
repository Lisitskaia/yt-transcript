from fastapi import FastAPI
from youtube_transcript_api import YouTubeTranscriptApi

app = FastAPI()

@app.get("/transcript/{video_id}")
def grab(video_id: str, lang: str = "ru,en"):
    prefs = lang.split(",")
    tr_list = YouTubeTranscriptApi.list_transcripts(video_id)
    for code in prefs:
        for mode in ("find_manually_created_transcript", "find_generated_transcript"):
            try:
                t = getattr(tr_list, mode)([code])
                return {"language": code, "segments": t.fetch()}
            except:
                pass
    return {"error": "no transcript"}
