# Use an official Python runtime as a parent image
FROM python:3.7.2-slim

# Set the working directory to /record
WORKDIR /app

# Copy the current directory contents into the container at /record
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Run record.py when the container launches
CMD ["python", "app.py"]

# set timezone
#ENV TZ=Asia/Singapore
#RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
