const API_BASE_URL = window.location.origin;

class APIClient {
    constructor() {
        this.ws = null;
        this.wsCallbacks = {};
    }

    // Health Check
    async healthCheck() {
        try {
            const response = await fetch(`${API_BASE_URL}/api/health`);
            return await response.json();
        } catch (error) {
            console.error('Health check failed:', error);
            return { status: 'offline' };
        }
    }

    // Employee APIs
    async getEmployees() {
        try {
            const response = await fetch(`${API_BASE_URL}/api/employees`);
            if (!response.ok) throw new Error('Failed to fetch employees');
            return await response.json();
        } catch (error) {
            console.error('Error fetching employees:', error);
            throw error;
        }
    }

    async getEmployee(employeeId) {
        try {
            const response = await fetch(`${API_BASE_URL}/api/employees/${employeeId}`);
            if (!response.ok) throw new Error('Employee not found');
            return await response.json();
        } catch (error) {
            console.error('Error fetching employee:', error);
            throw error;
        }
    }

    async createEmployee(data) {
        try {
            const response = await fetch(`${API_BASE_URL}/api/employees`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to create employee');
            }
            return await response.json();
        } catch (error) {
            console.error('Error creating employee:', error);
            throw error;
        }
    }

    async updateEmployee(employeeId, data) {
        try {
            const response = await fetch(`${API_BASE_URL}/api/employees/${employeeId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });
            if (!response.ok) throw new Error('Failed to update employee');
            return await response.json();
        } catch (error) {
            console.error('Error updating employee:', error);
            throw error;
        }
    }

    async deleteEmployee(employeeId) {
        try {
            const response = await fetch(`${API_BASE_URL}/api/employees/${employeeId}`, {
                method: 'DELETE'
            });
            if (!response.ok) throw new Error('Failed to delete employee');
            return true;
        } catch (error) {
            console.error('Error deleting employee:', error);
            throw error;
        }
    }

    // Face Registration
    async registerFace(employeeId, imageBase64, pose) {
        try {
            const response = await fetch(`${API_BASE_URL}/api/auto-registration/register-face`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    employee_id: employeeId,
                    image: imageBase64,
                    pose: pose
                })
            });
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to register face');
            }
            return await response.json();
        } catch (error) {
            console.error('Error registering face:', error);
            throw error;
        }
    }

    // Head Pose Detection
    async detectHeadPose(imageBase64) {
        try {
            const response = await fetch(`${API_BASE_URL}/api/head-pose/detect`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    image: imageBase64
                })
            });
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to detect head pose');
            }
            return await response.json();
        } catch (error) {
            console.error('Error detecting head pose:', error);
            throw error;
        }
    }

    // Train Model
    async trainModel(employeeId) {
        try {
            const response = await fetch(`${API_BASE_URL}/api/employees/${employeeId}/train`, {
                method: 'POST'
            });
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to train model');
            }
            return await response.json();
        } catch (error) {
            console.error('Error training model:', error);
            throw error;
        }
    }

    // Attendance APIs
    async getAttendance(date = null) {
        try {
            const url = date 
                ? `${API_BASE_URL}/api/attendance?date=${date}`
                : `${API_BASE_URL}/api/attendance`;
            const response = await fetch(url);
            if (!response.ok) throw new Error('Failed to fetch attendance');
            return await response.json();
        } catch (error) {
            console.error('Error fetching attendance:', error);
            throw error;
        }
    }

    // WebSocket for Recognition
    connectRecognition(onMessage, onError) {
        const wsUrl = `ws://${window.location.host}/api/recognition/ws/frontend-stream`;
        
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            console.log('WebSocket connected for recognition');
        };
        
        this.ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (onMessage) onMessage(data);
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            if (onError) onError(error);
        };
        
        this.ws.onclose = () => {
            console.log('WebSocket disconnected');
        };
        
        return this.ws;
    }

    sendFrame(imageBase64) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                type: 'recognition',
                image: imageBase64
            }));
        }
    }

    disconnectRecognition() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }
}

// Export for use in other scripts
window.APIClient = APIClient;
