from flask import Flask, render_template, request, send_file, after_this_request
import yt_dlp
import os
import uuid

app = Flask(__name__)
DOWNLOAD_FOLDER = 'downloads'

if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download-single', methods=['POST'])
def download_single():
    data = request.json
    video_url = data.get('url')
    format_type = data.get('format')
    quality = data.get('quality')

    unique_id = str(uuid.uuid4())[:8]
    output_path = os.path.join(DOWNLOAD_FOLDER, f'{unique_id}_%(title)s.%(ext)s')

    ydl_opts = {
        'outtmpl': output_path,
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
    }

    if format_type == 'mp3':
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': quality,
            }],
        })
    else:
        ydl_opts.update({
            'format': f'bestvideo[height<={quality}][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'merge_output_format': 'mp4',
        })

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            filename = ydl.prepare_filename(info)
            if format_type == 'mp3':
                filename = os.path.splitext(filename)[0] + '.mp3'

        @after_this_request
        def remove_file(response):
            try:
                os.remove(filename)
            except:
                pass
            return response

        return send_file(filename, as_attachment=True)
    except Exception as e:
        return {"error": str(e)}, 400

if __name__ == '__main__':
    app.run(debug=True, threaded=True ,host="0.0.0.0")