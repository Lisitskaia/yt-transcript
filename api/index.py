from fastapi import FastAPI
from youtube_transcript_api import YouTubeTranscriptApi

app = FastAPI()

@app.get("/transcript/{video_id}")
def get_transcript(video_id: str, lang: str = "ru,en"):
    prefs = lang.split(",")
    tr = YouTubeTranscriptApi.list_transcripts(video_id)
    for code in prefs:
        try:
            t = tr.find_manually_created_transcript([code])
            return {"language": code, "segments": t.fetch()}
        except:
            try:
                t = tr.find_generated_transcript([code])
                return {"language": code, "segments": t.fetch()}
            except:
                continue
    return {"error": "no transcript"}
