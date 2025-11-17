pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                // Jenkins already checks out when using "Pipeline script from SCM"
                // but we keep this for clarity
                checkout scm
            }
        }

        stage('Set up Python') {
            steps {
                sh 'python3 --version'
                // create venv if not exists
                sh 'python3 -m venv venv || true'
                sh '. venv/bin/activate && python3 -m pip install --upgrade pip'
            }
        }

        stage('Install dependencies') {
            steps {
                sh '. venv/bin/activate && pip install -r requirements.txt'
            }
        }

        stage('Lint with Pylint') {
    steps {
        // Run pylint but do not fail the build on style warnings
        sh '. venv/bin/activate && pylint --exit-zero app.py'
    }
}


        stage('Run tests') {
    steps {
        // Ensure Python can import app.py from the repo root
        sh '. venv/bin/activate && PYTHONPATH=. pytest'
    }
}


        stage('Run pip-audit') {
    steps {
        // Run pip-audit, but don't fail the build if vulnerabilities are found
        sh '. venv/bin/activate && pip install pip-audit && pip-audit || true'
    }
}

    }
}
