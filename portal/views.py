from django.shortcuts import render, redirect

from config import settings
from core import Chain
import os

def index(request):
    return render(request, "portal/index.html")

def apply(request):
    return render(request, "portal/apply.html")

def register(request):
    return render(request, "portal/register.html")

def data(request):
    return render(request, "portal/data.html")

def data(request):
    path = os.path.join(settings.BASE_DIR, "test.chain")

    if request.method == 'POST':
        patient_name = request.POST.get('patient_name')
        diagnosis = request.POST.get('diagnosis')

        chain = Chain.load(path)
        chain.add_block("medical_record", {"patient_name": patient_name, "diagnosis": diagnosis})
        chain.save(path)

        return redirect(request.path)

    if request.method == 'GET':
        if not os.path.exists(path):
            chain = Chain()
            chain.save(path)
            return render(request, 'portal/data.html', {'records': []})
        chain = Chain.load(path)
        records = []
        for b in chain:
            saved = b.hash
            recomputed = b.compute_hash()
            match = "OK" if saved == recomputed else "BROKEN"
            if b.index == 0:
                prev_link = "-"
            else:
                prev = chain.get_block(b.index - 1)
                prev_link = "OK" if b.header.prev_hash == prev.hash else "BROKEN"
            data = f"{b.index:>3} | " + f"{saved[:12]+'...':<14} | " f"{recomputed[:12]+'...':<14} | " + f"{match:<6} | "\
            + f"{prev_link:<9} | "\
            +f"{b.payload}"
            records.append({"patient_name": b.payload.get("patient_name"), "diagnosis": data});

    return render(request, 'portal/data.html', {'records': records})