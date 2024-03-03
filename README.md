# Building App.
docker build --no-cache -t resume-generator .

# Running App.
docker run -p 3000:3000 -p 5000:5000 resume-generator