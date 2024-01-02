from config import celery_app

if __name__ == '__main__':
    # log stuff about the configuration
    celery_app.start(['worker'])