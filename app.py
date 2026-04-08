from flask import Flask, render_template, request, send_file, after_this_request
import yt_dlp
import os
import uuid
import re

app = Flask(__name__)
DOWNLOAD_FOLDER = 'downloads'

if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

def get_unique_filename(base_path):

    if not os.path.exists(base_path):
        return base_path
    
    directory = os.path.dirname(base_path)
    filename = os.path.basename(base_path)
    name, ext = os.path.splitext(filename)
    
    counter = 1
    while True:
        new_filename = f"{name} ({counter}){ext}"
        new_path = os.path.join(directory, new_filename)
        if not os.path.exists(new_path):
            return new_path
        counter += 1

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download-single', methods=['POST'])
def download_single():
    data = request.json
    video_url = data.get('url')
    format_type = data.get('format')
    quality = data.get('quality')

    temp_opts = {'quiet': True, 'noplaylist': True}
    
    try:
        with yt_dlp.YoutubeDL(temp_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            video_title = info.get('title', 'video')
            video_title = re.sub(r'[\\/*?:"<>|]', "", video_title)

        ext = 'mp3' if format_type == 'mp3' else 'mp4'
        base_filename = os.path.join(DOWNLOAD_FOLDER, f"{video_title}.{ext}")
        
        final_path = get_unique_filename(base_filename)
        
        ydl_opts = {
            'outtmpl': final_path.replace('.mp3', '.%(ext)s') if format_type == 'mp3' else final_path,
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

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])

        @after_this_request
        def remove_file(response):
            try:
                if os.path.exists(final_path):
                    os.remove(final_path)
            except Exception as e:
                print(f"Error deleting file: {e}")
            return response

        return send_file(final_path, as_attachment=True)

    except Exception as e:
        return {"error": str(e)}, 400

if __name__ == '__main__':
    app.run(debug=True, threaded=True, host="0.0.0.0")