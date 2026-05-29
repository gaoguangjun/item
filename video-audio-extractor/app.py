"""
Video Audio Extractor - Web Application
从视频中提取音频的 Web 应用
"""
import os
import uuid
import zipfile
from io import BytesIO
from flask import Flask, render_template, request, send_file, jsonify
from moviepy.editor import VideoFileClip

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = None  # 无文件大小限制
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'output'

# 支持的视频格式
SUPPORTED_VIDEO_FORMATS = {
    'mp4': 'MP4 Video',
    'avi': 'AVI Video',
    'mov': 'QuickTime Video',
    'mkv': 'Matroska Video',
    'webm': 'WebM Video',
    'flv': 'Flash Video',
    'wmv': 'Windows Media Video',
    'm4v': 'iTunes Video',
    'mpeg': 'MPEG Video',
    'mpg': 'MPEG Video',
}

# 支持的音频格式
SUPPORTED_AUDIO_FORMATS = {
    'mp3': 'MP3 Audio',
    'wav': 'WAV Audio',
    'aac': 'AAC Audio',
    'm4a': 'M4A Audio',
    'ogg': 'OGG Audio',
    'flac': 'FLAC Audio',
}


@app.route('/')
def index():
    """主页面"""
    return render_template('index.html',
                         video_formats=SUPPORTED_VIDEO_FORMATS,
                         audio_formats=SUPPORTED_AUDIO_FORMATS)


@app.route('/api/formats')
def get_formats():
    """获取支持的格式列表"""
    return jsonify({
        'video_formats': SUPPORTED_VIDEO_FORMATS,
        'audio_formats': SUPPORTED_AUDIO_FORMATS
    })


@app.route('/extract', methods=['POST'])
def extract_audio():
    """处理音频提取请求"""
    try:
        # 获取表单数据
        video_format = request.form.get('video_format', '')
        audio_format = request.form.get('audio_format', 'mp3')

        # 验证音频格式
        if audio_format not in SUPPORTED_AUDIO_FORMATS:
            return jsonify({'success': False, 'error': f'不支持的音频格式: {audio_format}'}), 400

        # 检查是否有文件上传
        if 'videos' not in request.files:
            return jsonify({'success': False, 'error': '没有上传文件'}), 400

        files = request.files.getlist('videos')
        if not files or files[0].filename == '':
            return jsonify({'success': False, 'error': '没有选择文件'}), 400

        results = []
        errors = []

        for file in files:
            # 生成唯一文件名
            file_id = str(uuid.uuid4())
            original_filename = file.filename

            # 处理文件夹上传时的路径问题，提取纯文件名
            display_filename = original_filename  # 用于显示的文件名（可能含路径）
            safe_filename = os.path.basename(original_filename)  # 安全的文件名（纯文件名）
            base_name = os.path.splitext(safe_filename)[0]

            # 保存上传文件
            upload_path = os.path.join(app.config['UPLOAD_FOLDER'], f'{file_id}_{safe_filename}')
            file.save(upload_path)

            try:
                # 提取音频
                output_filename = f'{base_name}.{audio_format}'
                output_path = os.path.join(app.config['OUTPUT_FOLDER'], f'{file_id}_{output_filename}')

                # 使用 moviepy 提取音频
                with VideoFileClip(upload_path) as video:
                    # 根据格式选择不同的 codec 参数
                    codec_params = _get_codec_params(audio_format)
                    video.audio.write_audiofile(output_path, **codec_params)

                results.append({
                    'original': display_filename,
                    'output': output_filename,
                    'download_id': file_id,
                    'size': os.path.getsize(output_path)
                })

            except Exception as e:
                errors.append({
                    'file': display_filename,
                    'error': str(e)
                })
            finally:
                # 清理上传文件
                if os.path.exists(upload_path):
                    os.remove(upload_path)

        return jsonify({
            'success': True,
            'results': results,
            'errors': errors,
            'total_files': len(files),
            'success_count': len(results),
            'error_count': len(errors)
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


def _get_codec_params(audio_format: str) -> dict:
    """根据音频格式获取 codec 参数"""
    params = {}

    if audio_format == 'mp3':
        params.update({'codec': 'libmp3lame', 'bitrate': '192k'})
    elif audio_format == 'aac':
        params.update({'codec': 'aac', 'bitrate': '192k'})
    elif audio_format == 'm4a':
        params.update({'codec': 'aac', 'bitrate': '192k'})
    elif audio_format == 'ogg':
        params.update({'codec': 'libvorbis', 'bitrate': '192k'})
    elif audio_format == 'flac':
        params.update({'codec': 'flac'})
    elif audio_format == 'wav':
        params.update({'codec': 'pcm_s16le'})

    return params


@app.route('/download/<file_id>/<filename>')
def download_file(file_id: str, filename: str):
    """下载提取的音频文件"""
    try:
        # 查找文件（支持文件名中有前缀的情况）
        output_folder = app.config['OUTPUT_FOLDER']
        for f in os.listdir(output_folder):
            if f.startswith(file_id) and f.endswith(filename):
                file_path = os.path.join(output_folder, f)
                return send_file(file_path, as_attachment=True, download_name=filename)

        return jsonify({'success': False, 'error': '文件不存在或已过期'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/cleanup', methods=['POST'])
def cleanup_files():
    """清理已下载的文件"""
    try:
        data = request.get_json()
        file_ids = data.get('file_ids', [])

        for file_id in file_ids:
            output_folder = app.config['OUTPUT_FOLDER']
            for f in os.listdir(output_folder):
                if f.startswith(file_id):
                    os.remove(os.path.join(output_folder, f))
                    break

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/batch-download-zip', methods=['POST'])
def batch_download_zip():
    """批量下载 - 打包为 ZIP"""
    try:
        data = request.get_json()
        file_ids = data.get('file_ids', [])

        if not file_ids:
            return jsonify({'success': False, 'error': '没有文件可下载'}), 400

        # 创建内存中的 ZIP 文件
        memory_file = BytesIO()

        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            output_folder = app.config['OUTPUT_FOLDER']

            for file_id in file_ids:
                # 查找文件
                for f in os.listdir(output_folder):
                    if f.startswith(file_id):
                        file_path = os.path.join(output_folder, f)
                        # 获取原始文件名（去掉前缀）
                        original_name = '_'.join(f.split('_')[1:]) if '_' in f else f
                        zf.write(file_path, original_name)
                        break

        memory_file.seek(0)

        # 生成 ZIP 文件名
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        zip_name = f'audio_extract_{timestamp}.zip'

        return send_file(
            memory_file,
            mimetype='application/zip',
            as_attachment=True,
            download_name=zip_name
        )

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    # 确保目录存在
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

    app.run(debug=True, host='0.0.0.0', port=8001)
