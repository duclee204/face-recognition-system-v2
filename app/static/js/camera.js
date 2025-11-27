class CameraManager {
    constructor() {
        this.stream = null;
        this.videoElement = null;
        this.canvasElement = null;
        this.currentDeviceId = null;
        this.devices = [];
    }

    async init(videoElementId, canvasElementId = null) {
        this.videoElement = document.getElementById(videoElementId);
        if (canvasElementId) {
            this.canvasElement = document.getElementById(canvasElementId);
        }
        
        await this.getDevices();
        await this.startCamera();
    }

    async getDevices() {
        try {
            const devices = await navigator.mediaDevices.enumerateDevices();
            this.devices = devices.filter(device => device.kind === 'videoinput');
            return this.devices;
        } catch (error) {
            console.error('Error getting devices:', error);
            return [];
        }
    }

    async startCamera(deviceId = null) {
        try {
            // Stop current stream if any
            this.stopCamera();

            const constraints = {
                video: {
                    width: { ideal: 1280 },
                    height: { ideal: 720 },
                    facingMode: 'user'
                }
            };

            if (deviceId) {
                constraints.video.deviceId = { exact: deviceId };
            }

            this.stream = await navigator.mediaDevices.getUserMedia(constraints);
            this.videoElement.srcObject = this.stream;
            
            // Get actual device ID
            const videoTrack = this.stream.getVideoTracks()[0];
            this.currentDeviceId = videoTrack.getSettings().deviceId;

            return true;
        } catch (error) {
            console.error('Error starting camera:', error);
            alert('Không thể truy cập camera. Vui lòng kiểm tra quyền truy cập.');
            return false;
        }
    }

    stopCamera() {
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }
    }

    async switchCamera() {
        if (this.devices.length <= 1) {
            alert('Chỉ có một camera được tìm thấy');
            return;
        }

        const currentIndex = this.devices.findIndex(d => d.deviceId === this.currentDeviceId);
        const nextIndex = (currentIndex + 1) % this.devices.length;
        const nextDevice = this.devices[nextIndex];

        await this.startCamera(nextDevice.deviceId);
    }

    captureFrame() {
        if (!this.videoElement || !this.canvasElement) {
            console.error('Video or canvas element not initialized');
            return null;
        }

        const context = this.canvasElement.getContext('2d');
        this.canvasElement.width = this.videoElement.videoWidth;
        this.canvasElement.height = this.videoElement.videoHeight;
        
        context.drawImage(this.videoElement, 0, 0);
        
        return this.canvasElement.toDataURL('image/jpeg', 0.8);
    }

    captureFrameWithoutCanvas() {
        // Create temporary canvas
        const tempCanvas = document.createElement('canvas');
        tempCanvas.width = this.videoElement.videoWidth;
        tempCanvas.height = this.videoElement.videoHeight;
        
        const context = tempCanvas.getContext('2d');
        context.drawImage(this.videoElement, 0, 0);
        
        return tempCanvas.toDataURL('image/jpeg', 0.8);
    }

    drawBoundingBox(box, name, color = '#00ff00') {
        if (!this.canvasElement) return;

        const context = this.canvasElement.getContext('2d');
        const scaleX = this.canvasElement.width / this.videoElement.videoWidth;
        const scaleY = this.canvasElement.height / this.videoElement.videoHeight;

        // Draw rectangle
        context.strokeStyle = color;
        context.lineWidth = 3;
        context.strokeRect(
            box.x * scaleX,
            box.y * scaleY,
            box.width * scaleX,
            box.height * scaleY
        );

        // Draw name label
        if (name) {
            context.fillStyle = color;
            context.fillRect(
                box.x * scaleX,
                (box.y - 25) * scaleY,
                context.measureText(name).width + 10,
                25
            );
            
            context.fillStyle = '#000';
            context.font = '16px Arial';
            context.fillText(name, (box.x + 5) * scaleX, (box.y - 5) * scaleY);
        }
    }

    clearCanvas() {
        if (!this.canvasElement) return;
        
        const context = this.canvasElement.getContext('2d');
        context.clearRect(0, 0, this.canvasElement.width, this.canvasElement.height);
    }
}

// Export for use in other scripts
window.CameraManager = CameraManager;
