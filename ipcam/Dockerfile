# Use an official Python runtime as a parent image
#FROM python:3.7.2
FROM jjanzic/docker-python3-opencv

# Set the working directory to /record
WORKDIR /app

# Copy the current directory contents into the container at /record
COPY . /app

#RUN apt-get update \
#    && apt-get install -y \
#        build-essential

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Run record.py when the container launches
CMD ["python", "app.py"]

# set timezone
#ENV TZ=Asia/Singapore
#RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
