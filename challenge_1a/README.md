cd challenge_1a

docker build -t pdf-extractor:latest .

 docker run --rm -v ${PWD}/input:/app/input -v ${PWD}/output:/app/output --network none pdf-extractor:latest
