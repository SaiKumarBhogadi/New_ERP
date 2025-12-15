pipeline {
    agent any

    environment {
        // Repository URLs
        BACKEND_REPO = "https://github.com/vasavamshi-vv/New_ERP_Backend.git"
        FRONTEND_REPO = "https://github.com/vasavamshi-vv/ERP_Frontend_Project.git"

        // Workspace Directories
        BACKEND_DIR = "\${WORKSPACE}/erp-backend"
        FRONTEND_DIR = "\${WORKSPACE}/erp-frontend"

        // Docker Image & Container Names
        BACKEND_IMAGE = "erp-backend:dev"
        FRONTEND_IMAGE = "erp-frontend:dev"
        BACKEND_CONTAINER = "erp-backend-dev"
        FRONTEND_CONTAINER = "erp-frontend-dev"
    }

    stages {
        
        // --- THIS STAGE IS CORRECTED FOR VARIABLE RESOLUTION ---
        stage('Checkout Both Repos') {
            steps {
                echo "📥 Cloning backend & frontend..."

                // CORRECTED: Using literal directory names and env.VARIABLE syntax
                dir("erp-backend") { 
                    git branch: 'dev', url: env.BACKEND_REPO
                }
                dir("erp-frontend") { 
                    git branch: 'dev', url: env.FRONTEND_REPO
                }
            }
        }
        // --- END OF CORRECTION ---

        stage('Build Backend Docker Image') {
            steps {
                script {
                    echo "🐳 Building backend Docker image (NO CACHE)..."
                    sh """
                        cd \${BACKEND_DIR}
                        # CRITICAL FIX: --no-cache bypasses old image layer that had the sqlite3 settings
                        sudo docker build --no-cache -t \${BACKEND_IMAGE} .
                    """
                }
            }
        }

        stage('Deploy Backend Container') {
            steps {
                script {
                    echo "🚀 Deploying backend container (Connecting to RDS)..."
                    sh "sudo docker rm -f \${BACKEND_CONTAINER} || true"
                    sh """
                        sudo docker run -d \\
                            --name \${BACKEND_CONTAINER} \\
                            --network erp-network \\
                            --restart unless-stopped \\
                            -p 8000:8000 \\
                            --env-file "\${BACKEND_DIR}/erp_project/.env.dev" \\
                            -v "\${BACKEND_DIR}/erp_project/media:/app/media" \\
                            \${BACKEND_IMAGE}
                    """
                }
            }
        }

        stage('Build Frontend Docker Image') {
            steps {
                script {
                    echo "🌐 Building frontend Docker image..."
                    sh """
                        cd \${FRONTEND_DIR}
                        sudo docker build -t \${FRONTEND_IMAGE} .
                    """
                }
            }
        }

        stage('Deploy Frontend Container') {
            steps {
                script {
                    echo "🚀 Deploying frontend container (on Port 80)..."
                    sh "sudo docker rm -f \${FRONTEND_CONTAINER} || true"
                    sh """
                        sudo docker run -d \\
                            --name \${FRONTEND_CONTAINER} \\
                            --network erp-network \\
                            --restart unless-stopped \\
                            -p 80:80 \\
                            \${FRONTEND_IMAGE}
                    """
                }
            }
        }

        stage('Smoke Tests') {
            steps {
                sh """
                    echo "🧪 Running smoke tests..."
                    sleep 15
                    # Test Backend (Should succeed with RDS fix)
                    curl -sSf http://localhost:8000/api/login/ > /dev/null && echo "✔ Backend OK" || (echo "❌ Backend Down" && exit 1)
                    # Test Frontend
                    curl -sSf http://localhost:80 > /dev/null && echo "✔ Frontend OK" || (echo "❌ Frontend Down" && exit 1)
                """
            }
        }
    }

    post {
        success {
            echo "🎉 DEV CI/CD pipeline completed successfully!"
        }
        failure {
            echo "❌ Pipeline failed. Check logs in Jenkins!"
        }
    }
}
