pipeline {
    agent any

    environment {
        QA_SERVER_IP = "52.62.232.250"
        BACKEND_DIR = "${WORKSPACE}/erp_project"
        VENV_DIR = "${BACKEND_DIR}/venv"
        DEPLOY_USER = "ubuntu"
        DEPLOY_PATH = "/home/ubuntu/ERP-Backend-QA"
    }

    stages {
        stage('Checkout') {
            steps {
                echo "🔄 Checking out QA branch..."
                checkout scm
            }
        }

        stage('Setup Virtual Env & Dependencies') {
            steps {
                sh '''
                cd "${BACKEND_DIR}"
                if [ ! -d "${VENV_DIR}" ]; then
                    python3 -m venv "${VENV_DIR}"
                fi
                . "${VENV_DIR}/bin/activate"
                pip install --upgrade pip
                pip install -r requirements.txt
                '''
            }
        }

        stage('Run DB Migrations & Collectstatic') {
            steps {
                sh '''
                cd "${BACKEND_DIR}"
                . "${VENV_DIR}/bin/activate"
                python3 manage.py migrate --noinput
                python3 manage.py collectstatic --noinput || true
                '''
            }
        }

        stage('Restart Gunicorn (QA Server)') {
            steps {
                sh '''
                echo "Restarting Gunicorn QA service..."
                sudo systemctl restart gunicorn
                sudo systemctl status gunicorn --no-pager || true
                '''
            }
        }

        stage('Smoke Test') {
            steps {
                sh '''
                echo "Performing QA smoke test..."
                sleep 5
                curl -I http://127.0.0.1:8000/admin || { echo "Smoke test failed for QA"; exit 1; }
                '''
            }
        }
    }

    post {
        success {
            echo "✅ QA Backend Pipeline successful!"
        }
        failure {
            echo "❌ QA Backend Pipeline failed. Check logs."
        }
    }
}
