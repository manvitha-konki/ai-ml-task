import cv2
import pytesseract
from collections import defaultdict

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extract_headings_and_contents(image_path):
    image = cv2.imread(image_path)
    if image is None:
        print(f"Error: Unable to load image from {image_path}")
        return None

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT)

    headings = []
    contents = defaultdict(list)
    current_heading = None
    last_y = 0

    # First pass: identify headings
    for i in range(len(data['text'])):
        text = data['text'][i].strip()
        conf = int(data['conf'][i])
        x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]

        if conf > 60 and text:
            if h > 20 and (y > last_y + 20 or not headings):  # Heading criteria
                headings.append({
                    'text': text,
                    'coords': (x, y, x + w, y + h),
                    'y': y
                })
                current_heading = text
                last_y = y
            elif current_heading:
                contents[current_heading].append({
                    'text': text,
                    'coords': (x, y, x + w, y + h),
                    'y': y
                })

    # Sort headings by vertical position
    headings.sort(key=lambda h: h['y'])

    # Second pass: associate content with the nearest heading above it
    result = {}
    for i, heading in enumerate(headings):
        heading_text = heading['text']
        result[heading_text] = {
            'content': '',
            'coords': heading['coords'],
            'type': 'heading'
        }

        next_heading_y = headings[i+1]['y'] if i+1 < len(headings) else float('inf')
        
        for content in contents[heading_text]:
            if heading['y'] < content['y'] < next_heading_y:
                result[heading_text]['content'] += content['text'] + ' '

        result[heading_text]['content'] = result[heading_text]['content'].strip()

    # Draw rectangles and text on the image
    for heading, data in result.items():
        x1, y1, x2, y2 = data['coords']
        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 0, 255), 2)  # Red for headings
        cv2.putText(image, heading, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

        content_y = y2 + 10
        for word in data['content'].split():
            cv2.putText(image, word, (x1, content_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
            content_y += 20

    cv2.imwrite('output_image_with_boxes.jpg', image)
    return result

def main(image_path):
    headings_contents = extract_headings_and_contents(image_path)
    if headings_contents is not None:
        print("Extracted Headings and Contents:")
        for heading, data in headings_contents.items():
            print(f"\nHeading: {heading}")
            print(f"Content: {data['content']}")

image_path = "sample.jpeg"
main(image_path)