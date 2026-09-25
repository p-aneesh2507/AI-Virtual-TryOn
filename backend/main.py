from pathlib import Path
import asyncio
import shutil
import tempfile
import uuid
import traceback

from gradio_client import Client, handle_file
from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles


# --------------------------------------------------
# Configuration
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

GARMENT_DIR = (
    BASE_DIR.parent
    / "frontend"
    / "public"
    / "garments"
)

GENERATED_DIR = BASE_DIR / "generated"
GENERATED_DIR.mkdir(exist_ok=True)


# --------------------------------------------------
# Hugging Face IDM-VTON
# --------------------------------------------------

HF_SPACE = "yisol/IDM-VTON"

print()
print("=" * 60)
print("Connecting to Hugging Face IDM-VTON...")
print("=" * 60)

hf_client = Client(HF_SPACE)

print("Hugging Face IDM-VTON connected!")
print("=" * 60)
print()


# --------------------------------------------------
# Outfit catalogue
# --------------------------------------------------

OUTFITS = {
    1: {
        "file": "classic-black.png",
        "description": "black short sleeve crew neck t-shirt",
        "category": "upper_body",
    },
    2: {
        "file": "urban-blue.png",
        "description": "blue casual button-up shirt",
        "category": "upper_body",
    },
    3: {
        "file": "minimal-white.png",
        "description": "white short sleeve crew neck t-shirt",
        "category": "upper_body",
    },
    4: {
        "file": "street-style.png",
        "description": "black casual street style jacket",
        "category": "upper_body",
    },
}


# --------------------------------------------------
# FastAPI app
# --------------------------------------------------

app = FastAPI(
    title="AI Virtual Try-On API",
    description="Backend API for our AI Virtual Try-On hackathon project",
    version="3.0.0",
)


# --------------------------------------------------
# CORS
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://ai-virtual-try-on-jade.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------
# Serve generated images
# --------------------------------------------------

app.mount(
    "/generated",
    StaticFiles(directory=GENERATED_DIR),
    name="generated",
)


# --------------------------------------------------
# Basic routes
# --------------------------------------------------

@app.get("/")
def root():
    return {
        "status": "success",
        "message": "AI Virtual Try-On API is running!"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }


# --------------------------------------------------
# Upload test
# --------------------------------------------------

@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "message": "Image received successfully!"
    }


# --------------------------------------------------
# REAL AI VIRTUAL TRY-ON
# --------------------------------------------------

@app.post("/try-on")
async def try_on(
    request: Request,
    person_image: UploadFile = File(...),
    outfit_id: int = 0,
):

    # --------------------------------------------------
    # Validate outfit
    # --------------------------------------------------

    outfit = OUTFITS.get(outfit_id)

    if not outfit:
        raise HTTPException(
            status_code=400,
            detail="Invalid outfit selected."
        )


    # --------------------------------------------------
    # Validate uploaded image
    # --------------------------------------------------

    if not person_image.content_type:
        raise HTTPException(
            status_code=400,
            detail="No image content type received."
        )

    if not person_image.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="Please upload a valid image."
        )


    # --------------------------------------------------
    # Locate garment
    # --------------------------------------------------

    garment_path = GARMENT_DIR / outfit["file"]

    if not garment_path.exists():
        raise HTTPException(
            status_code=500,
            detail=f"Garment image not found: {outfit['file']}"
        )


    # --------------------------------------------------
    # Read person image
    # --------------------------------------------------

    person_bytes = await person_image.read()

    max_size = 10 * 1024 * 1024

    if len(person_bytes) > max_size:
        raise HTTPException(
            status_code=400,
            detail="Image is too large. Maximum size is 10MB."
        )


    # --------------------------------------------------
    # Create temporary person image
    # --------------------------------------------------

    suffix = (
        Path(person_image.filename or "person.jpg").suffix
        or ".jpg"
    )

    temp_person_file = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=suffix
    )

    temp_person_path = Path(temp_person_file.name)

    try:

        temp_person_file.write(person_bytes)
        temp_person_file.close()


        # --------------------------------------------------
        # Prepare ImageEditor input
        # --------------------------------------------------

        human_image_editor = {
    "background": handle_file(str(temp_person_path)),
    "layers": [],
    "composite": None,
}


        # --------------------------------------------------
        # Logging
        # --------------------------------------------------

        print()
        print("=" * 60)
        print("STARTING FREE AI VIRTUAL TRY-ON")
        print("=" * 60)
        print(f"Person image : {person_image.filename}")
        print(f"Outfit ID    : {outfit_id}")
        print(f"Garment      : {outfit['file']}")
        print(f"Description  : {outfit['description']}")
        print("=" * 60)
        print()
        print("Sending image to Hugging Face IDM-VTON...")
        print("Please wait...")
        print()


        # --------------------------------------------------
        # Run IDM-VTON through Hugging Face
        # --------------------------------------------------

        result = await asyncio.to_thread(
            hf_client.predict,

            human_image_editor,

            handle_file(str(garment_path)),

            outfit["description"],

            True,   # auto mask
            False,   # crop image to suitable ratio
            30,     # denoise steps
            42,     # seed

            api_name="/tryon",
        )


        # --------------------------------------------------
        # Read generated image
        # --------------------------------------------------

        print()
        print("Hugging Face response received!")
        print("Raw result:", result)
        print()


        if isinstance(result, (list, tuple)):
            output_image = result[0]
        else:
            output_image = result


        if not output_image:
            raise RuntimeError(
                "Hugging Face returned an empty image."
            )


        # --------------------------------------------------
        # Convert result into a local file
        # --------------------------------------------------

        result_filename = (
            f"tryon_{uuid.uuid4().hex}.png"
        )

        result_path = GENERATED_DIR / result_filename


        # Gradio normally returns a filepath
        if isinstance(output_image, str):

            source_path = Path(output_image)

            if source_path.exists():

                shutil.copy2(
                    source_path,
                    result_path
                )

            else:

                raise RuntimeError(
                    f"Generated image file not found: {output_image}"
                )

        else:

            # Some Gradio versions may return an object
            source_path = Path(str(output_image))

            if source_path.exists():

                shutil.copy2(
                    source_path,
                    result_path
                )

            else:

                raise RuntimeError(
                    f"Unable to locate generated image: {output_image}"
                )


        # --------------------------------------------------
        # Create browser-accessible URL
        # --------------------------------------------------

        result_url = str(
    request.base_url
) + f"generated/{result_filename}"


        print()
        print("=" * 60)
        print("AI TRY-ON COMPLETE!")
        print("=" * 60)
        print("Result:", result_url)
        print("=" * 60)
        print()


        return {
            "status": "success",
            "message": "Virtual try-on generated successfully!",
            "outfit_id": outfit_id,
            "outfit_name": outfit["file"],
            "result_url": result_url,
        }


    except Exception as error:
        print()
        print("=" * 60)
        print("AI TRY-ON ERROR")
        print("=" * 60)
        print(f"Error type: {type(error).__name__}")
        print(f"Error: {error}")
        print()
        traceback.print_exc()
        print("=" * 60)
        print()
        raise HTTPException(
            status_code=502,
            detail=f"AI try-on generation failed: {str(error)}"
        )


    finally:

        # Delete temporary uploaded person image
        try:
            temp_person_path.unlink(
                missing_ok=True
            )
        except Exception:
            pass