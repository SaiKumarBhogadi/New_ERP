pipeline {
    agent any

    environment {
        PROJECT_DIR = "/var/lib/jenkins/erp_backend_qa"
        VENV_DIR = "${PROJECT_DIR}/venv"
        APP_DIR = "${PROJECT_DIR}/erp_project"
        GUNICORN_SERVICE = "gunicorn"
    }

    stages {

        stage('📥 Pull Latest Code') {
            steps {
                echo "Fetching latest code from QA branch..."
                sh '''#!/bin/bash
                set -e
                if [ ! -d "$PROJECT_DIR" ]; then
                    sudo mkdir -p "$PROJECT_DIR"
                    sudo chown -R $(whoami):$(whoami) "$PROJECT_DIR"
                fi

                cd $PROJECT_DIR

                if [ ! -d "$APP_DIR" ]; then
                    git clone -b qa https://github.com/vasavamshi-vv/New_ERP_Backend.git erp_project
                else
                    cd $APP_DIR
                    git fetch origin qa
                    git reset --hard origin/qa
                fi
                '''
            }
        }

        stage('📦 Setup Virtual Environment & Install Dependencies') {
            steps {
                echo "Creating virtual environment and installing dependencies..."
                sh '''#!/bin/bash
                set -e
                cd $PROJECT_DIR

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
                echo "Restarting Gunicorn and Nginx services..."
                sh '''#!/bin/bash
                set -e

                echo "Restarting Gunicorn..."
                if sudo systemctl is-active --quiet $GUNICORN_SERVICE; then
                    sudo systemctl restart $GUNICORN_SERVICE
                else
                    sudo systemctl start $GUNICORN_SERVICE
                fi

                echo "Restarting Nginx..."
                if sudo systemctl is-active --quiet nginx; then
                    sudo systemctl restart nginx
                else
                    sudo systemctl start nginx
                fi

                sudo systemctl status $GUNICORN_SERVICE --no-pager
                sudo systemctl status nginx --no-pager
                '''
            }
        }

        stage('🧪 Smoke Test') {
            steps {
                echo "Running smoke test..."
                sh '''#!/bin/bash
                set -e
                sleep 5
                STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1/admin/)
                if [ "$STATUS" != "200" ] && [ "$STATUS" != "302" ]; then
                    echo "❌ Smoke test failed: backend not reachable (status $STATUS)"
                    exit 1
                fi
                echo "✅ Smoke test passed: backend reachable!"
                '''
            }
        }
    }

    post {
        success {
            echo "✅ QA Backend Deployed Successfully!"
        }
        failure {
            echo "❌ Deployment Failed — check Jenkins logs for details."
        }
    }
}
