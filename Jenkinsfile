pipeline {
    agent any

    environment {
        PROJECT_DIR = "/var/lib/jenkins/.jenkins/workspace/ERP-FullStack-Deploy/backend"
        VENV = "${PROJECT_DIR}/venv"
        PY = "${VENV}/bin/python3"
        PIP = "${VENV}/bin/pip"
        GUNICORN_SERVICE = "gunicorn"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Setup Virtual Environment & Install Requirements') {
            steps {
                sh '''
                    cd ${PROJECT_DIR}
                    python3 -m venv venv || true
                    . ${VENV}/bin/activate
                    ${PIP} install --upgrade pip
                    ${PIP} install -r requirements.txt
                '''
            }
        }

        stage('Migrate & Collectstatic') {
            steps {
                sh '''
                    . ${VENV}/bin/activate
                    cd ${PROJECT_DIR}
                    ${PY} manage.py migrate --noinput
                    ${PY} manage.py collectstatic --noinput
                '''
            }
        }

        stage('Restart Backend Services') {
            steps {
                sh '''
                    echo "Restarting Gunicorn and Nginx..."
                    sudo systemctl daemon-reload || true
                    sudo systemctl restart ${GUNICORN_SERVICE} || true
                    sudo systemctl restart nginx || true
                '''
            }
        }

        stage('Smoke Test') {
            steps {
                sh '''
                    echo "Checking backend health..."
                    sleep 2
                    STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/admin/)
                    echo "HTTP Status: $STATUS_CODE"
                '''
            }
        }
    }

    post {
        success {
            echo "✅ Backend pipeline succeeded!"
        }
        failure {
            echo "❌ Backend pipeline failed — check console logs!"
        }
    }
}
