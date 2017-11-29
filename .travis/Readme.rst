
docker build -f Dockerfile-build -t clairmeta/build_trusty .
docker run -it -v /Users/remi/Desktop/build:/deb clairmeta/build_trusty

docker build -f Dockerfile-install -t clairmeta/install_trusty .
docker run -it -v /Users/remi/Desktop/TESTS:/dcp clairmeta/install_trusty

