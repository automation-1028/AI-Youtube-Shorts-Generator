from flask import Flask, request, jsonify
from Components.YoutubeDownloader import download_youtube_video
from Components.Edit import extractAudio, crop_video
from Components.Transcription import transcribeAudio
from Components.LanguageTasks import GetHighlight
from Components.FaceCrop import crop_to_vertical, combine_videos
import os

app = Flask(__name__)

@app.route('/process-video', methods=['POST'])
def process_video():
    try:
        data = request.get_json()
        url = data.get('url')
        if not url:
            return jsonify({'error': 'URL is required'}), 400

        title, Vid = download_youtube_video(url)
        if not Vid:
            return jsonify({'error': 'Unable to download the video'}), 400

        Vid = Vid.replace(".webm", ".mp4")
        Audio = extractAudio(Vid)
        
        if not Audio:
            return jsonify({'error': 'No audio file found'}), 400

        transcriptions = transcribeAudio(Audio)
        if not transcriptions:
            return jsonify({'error': 'No transcriptions found'}), 400

        TransText = ""
        for text, start, end in transcriptions:
            TransText += (f"{start} - {end}: {text}")

        start, stop = GetHighlight(TransText)
        if start == 0 or stop == 0:
            return jsonify({'error': 'Error in getting highlight'}), 400

        output_path = f"output_{os.urandom(8).hex()}.mp4"
        temp_output = "Out.mp4"
        cropped = "cropped.mp4"

        crop_video(Vid, temp_output, start, stop)
        crop_to_vertical(temp_output, cropped)
        combine_videos(temp_output, cropped, output_path)

        print(title, output_path)
        return jsonify({
            'title': title,
            'output_path': output_path
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)