import numpy as np
import soundfile as sf
import librosa
import pyrubberband as pyrb
from pydub import AudioSegment
from youtube_transcript_api import YouTubeTranscriptApi
from googletrans import Translator
from moviepy.editor import *
import moviepy
import requests
import os
import subprocess
from multiprocessing import Pool
from secrets import bnkey


def get_and_translate_srt(youtubeid):
    translator = Translator()
    #srt = YouTubeTranscriptApi.get_transcript(youtubeid)
    transcript_list = YouTubeTranscriptApi.list_transcripts(youtubeid)
    transcript_list
    transcript = transcript_list.find_transcript(['en'])
    etrans = transcript.fetch()
    translated_transcript = transcript.translate('th')
    ttrans = translated_transcript.fetch()
    return ttrans
    eDic = {}
    for i in range(len(etrans)):
        etime = etrans[i]['start']
        eDic[etime] = etrans[i]
    tDic = {}
    for i in range(len(ttrans)):
        ttime = ttrans[i]['start']
        tDic[ttime] = ttrans[i]

    for k in eDic.keys():
        try:
            eDic[k]['text'] = eDic[k]['text'] + ' - ' + tDic[k]['text']
        except:
            pass
    return eDic
    # ttrans

    # srtt = srt.copy()
    # for i in range(len(srt)):
    #   #print(i)
    #   if i%10==0:
    #     print('%.2f%%'%((i/len(srt))*100))
    #   srtt[i]['text'] = translator.translate(srt[i]['text'],dest='th').text
    # return srtt


def get_Durations(yt_trans):
    durations = []
    for i in range(len(yt_trans)-1):
        durations.append(yt_trans[i+1]['start']-yt_trans[i]['start'])
    durations.append(yt_trans[-1]['duration'])
    return durations


def replace_words(srtt, rDict):
    for rw in rDict.keys():
        for i in range(len(srtt)):
            srtt[i]['text'] = srtt[i]['text'].replace(rw, rDict[rw])
    return srtt


def botnoi_voice(sentence):
    url = "https://voice.botnoi.ai/api/service/generate_audio"
    payload = {"text": sentence, "speaker": speaker,
               "volume": 1, "speed": speed, "type_media": "mp3"}
    headers = {
        'Botnoi-Token': bnkey
    }
    response = requests.request("POST", url, headers=headers, json=payload)
    return response.json()['audio_url']


def read_stt(sttList):
    tList = [stt['text'] for stt in sttList]  # transcript list
    aList = multi_stt(tList)  # audio list
    for i in range(len(aList)):
        # add audio url to dict in transcript list
        sttList[i]['audio'] = aList[i]
    return sttList


def read_stt_single(text):
    audioUrl = botnoi_voice(text)
    return audioUrl


def multi_stt(textList):
    pool = Pool(5)
    res = pool.map(read_stt_single, textList)
    return res  # audio list


def DownloadFile(url, fn):
    #local_filename = 'test.mp3'
    r = requests.get(url)
    with open(fn, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:  # filter out keep-alive new chunks
                f.write(chunk)


def change_duration(y, sr, target):
    old_duration = librosa.get_duration(y=y, sr=sr)
    return pyrb.time_stretch(y, sr, old_duration/target)


def wav_to_mp3(filename):
    AudioSegment.from_wav(filename).export(
        f"{filename[:-4]}.mp3", format="mp3")
    os.remove(filename)


def mergeaudio(astt):
    cl = []
    e_durations = get_Durations(astt)
    for i in range(len(astt)):
        # print(i)
        if i % 10 == 0:
            print('%.2f%%' % ((i/len(astt))*100))
        afurl = astt[i]['audio']
        fn = afurl.split('_')[-1]
        DownloadFile(afurl, fn)
        # --- inject code to time stretching ---
        y, sr = librosa.load(fn)
        if e_durations[i] < librosa.get_duration(y=y, sr=sr):
            sf.write(f"{fn[:-4]}_e.wav",
                     change_duration(y, sr, e_durations[i]), sr)
            wav_to_mp3(f"{fn[:-4]}_e.wav")
        else:
            os.rename(fn, f"{fn[:-4]}_e.mp3")
        # ---------------------------------
        audio = AudioFileClip(f"{fn[:-4]}_e.mp3")
        st = astt[i]['start']
        cl.append(audio.set_start(st))
    mcl = moviepy.audio.AudioClip.CompositeAudioClip(cl)
    return mcl


def pipeline(youtubeurl, outfile="myfilename.mp4"):
    yid = youtubeurl.split('=')[1]
    videoclip = VideoFileClip("myvid9.mp4")
    #srtt = get_and_translate_srt(yid)
    #srtt = tList
    # rDict = {}
    # rDict['\n']=' '
    # rDict['ฉัน'] = 'ผม'
    # rDict['โฆษณา'] = 'กระแส'
    # rDict['AI'] = 'เอไอ'
    #rDict = replace_words(srtt,rDict)
    # return rDict

    astt = read_stt(rest)
    mcl = mergeaudio(astt)
    videoclip.audio = mcl
    videoclip.write_videofile(outfile, codec='libx264', audio_codec='aac',
                              temp_audiofile='temp-audio.m4a', remove_temp=True)


if __name__ == '__main__':
    rest = get_and_translate_srt('aircAruvnKk')
    speaker = '40'
    speed = 1
    pipeline("https://www.youtube.com/watch?v=aircAruvnKk", "out_myvid9.mp4")
