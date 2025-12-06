document.addEventListener('DOMContentLoaded', function() {
    
    // 1. Initialize searchable dropdown
    const locationEl = document.getElementById('location');
    const locationChoice = new Choices(locationEl, {
        searchEnabled: true,
        itemSelectText: '',
        shouldSort: false, // Keep alphabetical from backend
    });

    // 2. Data & Elements
    const dataCombinations = window.datasetCombinations || [];
    
    const els = {
        area: document.getElementById('area_type'),
        zone: document.getElementById('zone_name'),
        form: document.getElementById('predictionForm'),
        btn: document.getElementById('predictBtn'),
        
        // Result Panel Views
        panelEmpty: document.getElementById('emptyState'),
        panelLoading: document.getElementById('loading'),
        panelSuccess: document.getElementById('successState'),
        panelError: document.getElementById('errorState'),
        
        // Output Fields
        outLakhs: document.getElementById('priceLakhs'),
        outCrores: document.getElementById('priceCrores'),
        outSqft: document.getElementById('pricePerSqft'),
        errorMsg: document.getElementById('errorMsg')
    };

    // 3. Logic: Update Area Types
    locationEl.addEventListener('change', () => {
        const loc = locationEl.value;
        
        // Reset Dependent Fields
        els.area.innerHTML = '<option value="">Select Location First</option>';
        els.zone.innerHTML = '<option value="">Select Area Type First</option>';
        els.area.disabled = true;
        els.zone.disabled = true;

        if (!loc) return;

        const validAreas = [...new Set(
            dataCombinations
                .filter(i => i.location === loc)
                .map(i => i.area_type)
        )].sort();

        if (validAreas.length) {
            els.area.innerHTML = '<option value="">Select Area Type</option>';
            validAreas.forEach(area => {
                els.area.add(new Option(area, area));
            });
            els.area.disabled = false;
        } else {
            els.area.innerHTML = '<option value="">No options available</option>';
        }
    });

    // 4. Logic: Update Zones
    els.area.addEventListener('change', () => {
        const loc = locationEl.value;
        const area = els.area.value;
        
        els.zone.innerHTML = '<option value="">Select Zone</option>';
        els.zone.disabled = true;

        if (!loc || !area) return;

        const validZones = [...new Set(
            dataCombinations
                .filter(i => i.location === loc && i.area_type === area)
                .map(i => i.zone_name)
        )].sort();

        if (validZones.length) {
            validZones.forEach(zone => {
                els.zone.add(new Option(zone, zone));
            });
            els.zone.disabled = false;
        }
    });

    // 5. Logic: Handle Predict
    els.form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // Set Loading State
        toggleState('loading');
        els.btn.disabled = true;

        const formData = {
            location: locationEl.value,
            area_type: els.area.value,
            zone_name: els.zone.value,
            availability: 'Ready To Move',
            bhk: document.getElementById('bhk').value,
            total_sqft: document.getElementById('total_sqft').value,
            bath: document.getElementById('bath').value,
            balcony: document.getElementById('balcony').value
        };

        try {
            // Validate combination locally first
            const exists = dataCombinations.some(i => 
                i.location === formData.location && 
                i.area_type === formData.area_type && 
                i.zone_name === formData.zone_name
            );

            if (!exists) throw new Error("This combination of Location, Area, and Zone is not in our records.");

            const res = await fetch('/predict', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });

            const data = await res.json();

            if (data.success) {
                els.outLakhs.textContent = `₹${data.predicted_price.toFixed(2)} L`;
                els.outCrores.textContent = `₹${data.price_in_crores.toFixed(2)} Cr`;
                els.outSqft.textContent = `₹${data.price_per_sqft}`;
                toggleState('success');
            } else {
                throw new Error(data.error || 'Prediction failed');
            }
        } catch (err) {
            els.errorMsg.textContent = err.message;
            toggleState('error');
        } finally {
            els.btn.disabled = false;
        }
    });

    // Helper to switch panel views
    function toggleState(state) {
        els.panelEmpty.classList.add('hidden');
        els.panelLoading.classList.add('hidden');
        els.panelSuccess.classList.add('hidden');
        els.panelError.classList.add('hidden');

        if (state === 'loading') els.panelLoading.classList.remove('hidden');
        if (state === 'success') els.panelSuccess.classList.remove('hidden');
        if (state === 'error') els.panelError.classList.remove('hidden');
        if (state === 'empty') els.panelEmpty.classList.remove('hidden');
    }
});