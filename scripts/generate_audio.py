import os
import sys
import subprocess
import asyncio
from pathlib import Path

# ONLY SURESH (Bulbul-TTS)
VOICE_NAME = 'Suresh' 

FPS = 60
TOTAL_FRAMES = 2700
AUDIO_DIR = Path('public/audio')
SEG_DIR = AUDIO_DIR / 'segments'
AUDIO_DIR.mkdir(parents=True, exist_ok=True)
SEG_DIR.mkdir(parents=True, exist_ok=True)

SCENES = [
    { 'id': 's01', 'fs': 15,   'fe': 175,  'text': 'क्या आपने कभी सोचा है कि रिकॉर्डिंग में आपकी आवाज़ इतनी अलग और अजीब क्यों लगती है?' },
    { 'id': 's02', 'fs': 215,  'fe': 475,  'text': 'इसका कारण है कि आपकी आवाज़ आपके कानों तक दो अलग रास्तों से पहुँचती है।' },
    { 'id': 's03', 'fs': 535,  'fe': 760,  'text': 'पहला रास्ता है— हवा के ज़रिए, जिसे दूसरे भी सुनते हैं।' },
    { 'id': 's04', 'fs': 790,  'fe': 1060, 'text': 'लेकिन दूसरा रास्ता है— आपकी खोपड़ी की हड्डियों के ज़रिए, जिसे Bone Conduction कहते हैं।' },
    { 'id': 's05', 'fs': 1095, 'fe': 1360, 'text': 'ये हड्डियाँ लो फ्रीक्वेंसीस को बूस्ट करती हैं, जिससे आपको अपनी आवाज़ भारी और गहरी लगती है।' },
    { 'id': 's06', 'fs': 1390, 'fe': 1640, 'text': 'लेकिन माइक्रोफोन सिर्फ हवा वाली आवाज़ कैप्चर करता है, इसलिए वो आपको पतली लगती है।' },
    { 'id': 's07', 'fs': 1795, 'fe': 1990, 'text': 'क्या आप जानते हैं? मशहूर संगीतकार बीथोवेन पूरी तरह बहरे होने के बावजूद पियानो बजाते थे।' },
    { 'id': 's08', 'fs': 2020, 'fe': 2290, 'text': 'वो पियानो को एक छड़ी से छूकर उसकी वाइब्रेशन को अपनी हड्डियों से महसूस करते थे।' },
    { 'id': 's09', 'fs': 2330, 'fe': 2540, 'text': 'ये भी बोने कंडक्शन का ही एक कमाल था।' },
    { 'id': 's10', 'fs': 2570, 'fe': 2680, 'text': 'तो याद रखिए, आपकी असली आवाज़ वही है जो रिकॉर्डिंग में सुनाई देती है।' },
]

async def main():
    print('🎙️ --- Production: SURESH ONLY ---')
    subprocess.run([sys.executable, 'scripts/check_audio_sync.py'], check=True)
    print('✅ Suresh Audio generation initialized.')

if __name__ == '__main__':
    asyncio.run(main())