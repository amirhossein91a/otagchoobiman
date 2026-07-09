from jnius import autoclass
from time import sleep

# کلاس‌های اندرویدی مورد نیاز
PythonService = autoclass('org.kivy.android.PythonService')
service = PythonService.mService

def start_notification():
    Context = autoclass('android.content.Context')
    Intent = autoclass('android.content.Intent')
    PendingIntent = autoclass('android.app.PendingIntent')
    NotificationBuilder = autoclass('android.app.Notification$Builder')
    NotificationManager = autoclass('android.app.NotificationManager')
    NotificationChannel = autoclass('android.app.NotificationChannel')
    
    channel_id = 'music_service'
    channel_name = 'Music Player'
    
    # ساخت کانال نوتیفیکیشن (برای اندروید 8 به بالا)
    importance = NotificationManager.IMPORTANCE_LOW
    channel = NotificationChannel(channel_id, channel_name, importance)
    notification_manager = service.getSystemService(Context.NOTIFICATION_SERVICE)
    notification_manager.createNotificationChannel(channel)
    
    # ساخت اینتنت برای باز شدن اپلیکیشن با کلیک روی نوتیفیکیشن
    app_context = service.getApplication().getApplicationContext()
    app_intent = Intent(app_context, autoclass('org.kivy.android.PythonActivity'))
    pending_intent = PendingIntent.getActivity(app_context, 0, app_intent, PendingIntent.FLAG_IMMUTABLE)
    
    # طراحی نوتیفیکیشن
    builder = NotificationBuilder(service, channel_id)
    builder.setContentTitle('اتاق چوبی')
    builder.setContentText('در حال پخش موسیقی...')
    builder.setSmallIcon(service.getApplicationInfo().icon)
    builder.setContentIntent(pending_intent)
    builder.setOngoing(True)
    
    # اجرای سرویس در حالت Foreground (باعث می‌شود اندروید اپ را نبندد)
    notification = builder.build()
    service.startForeground(1, notification)

if __name__ == '__main__':
    start_notification()
    while True:
        # اینجا بعداً می‌توانیم منطق دریافت دستورات Play/Pause از نوتیفیکیشن را اضافه کنیم
        sleep(1)
