import numpy as np
import cv2
from PIL import Image
import io
import base64
from openai import OpenAI
from dotenv import load_dotenv
import os
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPainter
import re
from datetime import datetime, timedelta

class ImageProcessor:
    def __init__(self):
        load_dotenv()
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        # Time pattern: matches "HH:MM" or "H:MM" format
        self.time_pattern = re.compile(r'\b([0-9]{1,2}):([0-5][0-9])\b')
        
    def parse_time(self, time_str):
        """Convert time string to minutes where format is H:MM"""
        if ':' in time_str:
            try:
                hours, minutes = map(int, time_str.split(':'))
                total_minutes = (hours * 60) + minutes
                return total_minutes
            except ValueError:
                return None
        return None
        
    def process_image(self, pixmap):
        # Convert QPixmap to bytes
        image = pixmap.toImage()
        
        # Convert QImage to bytes (keep existing conversion code)
        buffer = io.BytesIO()
        qsize = image.size()
        
        # Create QImage in RGB888 format
        temp_image = QImage(
            qsize.width(), 
            qsize.height(),
            QImage.Format.Format_RGB888
        )
        temp_image.fill(Qt.GlobalColor.white)
        
        # Draw the original image onto the RGB888 image
        painter = QPainter(temp_image)
        painter.drawImage(0, 0, image)
        painter.end()
        
        # Convert to PIL Image and get base64
        width = temp_image.width()
        height = temp_image.height()
        ptr = temp_image.bits()
        ptr.setsize(height * width * 3)
        arr = np.frombuffer(ptr, np.uint8).reshape((height, width, 3))
        pil_image = Image.fromarray(arr)
        
        # Save to buffer
        buffer = io.BytesIO()
        pil_image.save(buffer, format='PNG')
        image_bytes = buffer.getvalue()
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        
        try:
            # Process with OpenAI Vision API
            response = self.client.chat.completions.create(
                model="gpt-4o-mini-2024-07-18",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Extract all time durations, dates, or numeric patterns from this image. Return them exactly as they appear, one per line. Focus on time values in H:MM format, but also note any other relevant numeric patterns."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=300
            )
            
            # Extract text from response
            text = response.choices[0].message.content
            
            # Extract times using regex
            times_str = self.extract_times(text)
            times_minutes = [self.time_to_minutes(t) for t in times_str]
            
            # Calculate totals
            total_minutes = sum(times_minutes)
            
            return {
                "total": total_minutes,
                "average": total_minutes / len(times_minutes) if times_minutes else 0,
                "count": len(times_minutes),
                "times": times_minutes,
                "times_formatted": times_str,
                "total_formatted": self.minutes_to_time_str(total_minutes)
            }
            
        except Exception as e:
            print(f"Error processing image: {str(e)}")
            return {
                "total": 0,
                "average": 0,
                "count": 0,
                "times": [],
                "times_formatted": [],
                "error": str(e)
            }
    
    def time_to_minutes(self, time_str):
        """Convert time string (HH:MM) to total minutes"""
        try:
            hours, minutes = map(int, time_str.split(':'))
            return hours * 60 + minutes
        except (ValueError, AttributeError):
            return 0
            
    def minutes_to_time_str(self, total_minutes):
        """Convert total minutes to formatted time string (HH:MM)"""
        if total_minutes == 0:
            return "0:00"
        
        hours = total_minutes // 60
        minutes = total_minutes % 60
        return f"{hours}:{minutes:02d}"
    
    def extract_times(self, text):
        """Extract time values from text using regex"""
        if not text:
            return []
            
        matches = self.time_pattern.findall(text)
        times = []
        
        for hours, minutes in matches:
            # Validate hours and minutes
            try:
                h, m = int(hours), int(minutes)
                if 0 <= h <= 23 and 0 <= m <= 59:
                    times.append(f"{h}:{m:02d}")
            except ValueError:
                continue
                
        return times 