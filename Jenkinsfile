pipeline {
    agent any

    environment {
        APP_DIR = "/var/lib/jenkins/erp_backend_qa/erp_project"
        VENV_DIR = "/var/lib/jenkins/erp_backend_qa/venv"
        ENV_FILE = "/var/lib/jenkins/.env/erp_backend_qa.env"
    }

    stages {

        stage('📥 Pull Latest Code') {
            steps {
                echo "Fetching latest QA code..."
                git branch: 'qa', url: 'https://github.com/vasavamshi-vv/New_ERP_Backend.git'
            }
        }

        stage('📦 Setup Virtual Environment & Install Dependencies') {
            steps {
                echo "Setting up virtual environment..."
                sh '''#!/bin/bash
                set -e
                if [ ! -d "$VENV_DIR" ]; then
                    python3 -m venv $VENV_DIR
                fi
                source $VENV_DIR/bin/activate
                pip install --upgrade pip
                pip install -r $APP_DIR/requirements.txt
                deactivate
                '''
            }
        }

        stage('🧹 Apply Migrations & Collect Static Files') {
            steps {
                echo "Applying migrations and collecting static files..."
                sh '''#!/bin/bash
                set -e
                export $(grep -v '^#' $ENV_FILE | xargs)
                cd $APP_DIR
                source $VENV_DIR/bin/activate
                python3 manage.py migrate --noinput
                python3 manage.py collectstatic --noinput || true
                deactivate
                '''
            }
        }

        stage('🚀 Restart Gunicorn & Nginx') {
            steps {
                echo "Restarting backend services..."
                sh '''#!/bin/bash
                sudo systemctl restart gunicorn
                sudo systemctl restart nginx
                '''
            }
        }

        stage('🧪 Smoke Test') {
            steps {
                echo "Performing health check..."
                sh '''#!/bin/bash
                sleep 5
                curl -f http://127.0.0.1:8000/ || exit 1
                '''
            }
        }
    }

    post {
        success {
            echo "✅ ERP Backend QA deployed successfully!"
        }
        failure {
            echo "❌ Deployment failed. Check Jenkins logs for errors."
        }
    }
}
