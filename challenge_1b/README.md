cd challenge_1b

 docker build --platform linux/amd64 -t challenge1b:latest .     


 docker run --rm -v ${pwd}:/app/input -v ${pwd}/output:/app/output --network none challenge1b:latest
