from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.db import models
from wsgiref.util import FileWrapper
from .models import AudioRecording
import json
import base64
import os
import zipfile


# Updated speaker mapping with 3 new speakers
SPEAKER_MAPPING = {
    '(speaker1)': 'speaker1',
    

}

def get_speaker_filename(username, clip_number):
    """
    Generate consistent filename for a speaker's recording
    """
    speaker_id = SPEAKER_MAPPING.get(username, 'unknown')
    return f'{speaker_id}_input{clip_number}.wav'

def home(request):
    """
    Display the home page with user statistics.
    """
    users = [
        '(speaker1)']


    stats_dict = {}
    for user in users:
        recordings = AudioRecording.objects.filter(username=user)
        total_duration = recordings.aggregate(total=models.Sum('duration'))['total'] or 0
        stats_dict[user] = {
            'total_recordings': recordings.count(),
            'total_duration': round(total_duration, 1)
        }

    context = {
        'users': users,
        'user_stats': stats_dict
    }
    return render(request, 'recorder/home.html', context)

def record(request, username):
    """
    Display the recording page for a specific user.
    """
    recordings = AudioRecording.objects.filter(username=username)
    total_duration = recordings.aggregate(total=models.Sum('duration'))['total'] or 0

    context = {
        'username': username,
        'recordings': recordings,
        'total_duration': round(total_duration, 1),
        'total_recordings': recordings.count()
    }
    return render(request, 'recorder/record.html', context)

@csrf_exempt
def save_recording(request):
    """
    Handle saving of new audio recordings with the specified naming convention.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})

    try:
        data = json.loads(request.body)
        audio_data = data.get('audio')
        username = data.get('username')
        duration = float(data.get('duration', 5.0))

        if not audio_data or not username:
            return JsonResponse({'success': False, 'error': 'Missing required data'})

        # Get next input number for this speaker
        next_clip = AudioRecording.objects.filter(username=username).count() + 1

        # Generate filename using the consistent naming function
        filename = get_speaker_filename(username, next_clip)

        try:
            audio_data = base64.b64decode(audio_data.split(',')[1])
        except:
            return JsonResponse({'success': False, 'error': 'Invalid audio data'})

        # Create file path and ensure directory exists
        file_path = f'recordings/{filename}'
        full_path = os.path.join(settings.MEDIA_ROOT, file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        # Save audio file
        with open(full_path, 'wb') as f:
            f.write(audio_data)

        # Create recording record
        recording = AudioRecording.objects.create(
            username=username,
            clip_number=next_clip,
            audio_file=file_path,
            duration=duration
        )

        # Calculate total duration
        total_duration = AudioRecording.objects.filter(username=username).aggregate(
            total=models.Sum('duration'))['total'] or 0

        return JsonResponse({
            'success': True,
            'clip_number': next_clip,
            'filename': filename,
            'total_recordings': next_clip,
            'total_duration': round(total_duration, 1)
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@csrf_exempt
def clear_recordings(request, username):
    """
    Clear selected or all recordings for a user.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})

    try:
        recording_ids = request.POST.getlist('recording_ids')
        recordings = AudioRecording.objects.filter(username=username)

        if recording_ids:
            recordings = recordings.filter(id__in=recording_ids)

        # Delete files and records
        deleted_count = 0
        for recording in recordings:
            try:
                file_path = os.path.join(settings.MEDIA_ROOT, str(recording.audio_file))
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except OSError as e:
                        print(f"Error deleting file {file_path}: {e}")

                recording.delete()
                deleted_count += 1
            except Exception as e:
                print(f"Error deleting recording {recording.id}: {e}")
                continue

        # Get updated statistics
        remaining_recordings = AudioRecording.objects.filter(username=username)
        total_duration = remaining_recordings.aggregate(
            total=models.Sum('duration'))['total'] or 0

        return JsonResponse({
            'success': True,
            'message': f'Successfully deleted {deleted_count} recordings',
            'total_recordings': remaining_recordings.count(),
            'total_duration': round(total_duration, 1)
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

def download_user_recordings(request, username):
    """
    Download all recordings for a user as a zip file.
    """
    try:
        recordings = AudioRecording.objects.filter(username=username).order_by('clip_number')

        if not recordings.exists():
            return JsonResponse({
                'success': False,
                'error': 'No recordings found for this user'
            })

        # Create a zip file
        speaker_id = SPEAKER_MAPPING.get(username, 'unknown')
        zip_filename = f"{speaker_id}_recordings.zip"
        zip_path = os.path.join(settings.MEDIA_ROOT, zip_filename)

        with zipfile.ZipFile(zip_path, 'w') as zip_file:
            for recording in recordings:
                # Generate the correct filename for this recording
                proper_filename = get_speaker_filename(username, recording.clip_number)
                file_path = os.path.join(settings.MEDIA_ROOT, str(recording.audio_file))

                if os.path.exists(file_path):
                    # Use the proper filename instead of the original filename
                    zip_file.write(file_path, proper_filename)

        # Serve the zip file
        wrapper = FileWrapper(open(zip_path, 'rb'))
        response = HttpResponse(wrapper, content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename={zip_filename}'

        # Clean up the temporary zip file
        os.remove(zip_path)

        return response

    except Exception as e:
        if os.path.exists(zip_path):
            os.remove(zip_path)
        return JsonResponse({
            'success': False,
            'error': str(e)
        })