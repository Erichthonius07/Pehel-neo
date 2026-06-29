"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import { LayoutShell } from "@/components/layout/LayoutShell";
import { issuesApi } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { KANPUR_CENTER, KANPUR_WARDS, findNearestWard } from "@/data/kanpur-wards";
import { useRouter } from "next/navigation";

const MapPicker = dynamic(() => import("@/components/submission/MapPicker"), {
  ssr: false,
  loading: () => <div className="h-[400px] bg-surface-secondary flex items-center justify-center"><p className="mono-text">Loading map...</p></div>
});

export default function NewIssuePage() {
  const [step, setStep] = useState(1);
  const [wardId, setWardId] = useState("");
  const [lat, setLat] = useState(KANPUR_CENTER.lat);
  const [lng, setLng] = useState(KANPUR_CENTER.lng);
  const [category, setCategory] = useState("");
  const [severity, setSeverity] = useState("medium");
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const { citizenToken } = useAuth();
  const router = useRouter();

  const handleLocationSelect = (lat: number, lng: number) => {
    setLat(lat); setLng(lng);
    const nearest = findNearestWard(lat, lng);
    setWardId(nearest.id);
  };

  const handleSubmit = async () => {
    if (!citizenToken) return;
    setSubmitting(true);
    try {
      const ward = KANPUR_WARDS.find(w => w.id === wardId) || KANPUR_WARDS[0];
      const res = await issuesApi.create({
        category: category.toLowerCase(),
        ward_id: ward.id,
        title,
        description,
        geo_lat: lat,
        geo_lng: lng,
        location_text: ward.name,
        severity: severity.toLowerCase(),
        is_safety_risk: severity === 'CRITICAL',
      }, citizenToken);
      router.push(`/issues/${(res as {id: string}).id}`);
    } catch (e) { alert("Failed to submit"); }
    setSubmitting(false);
  };

  return (
    <LayoutShell>
      <h1 className="text-4xl font-extrabold text-text-primary mb-8">REPORT AN ISSUE</h1>

      <div className="max-w-[600px] mx-auto mb-12">
        <div className="flex items-center justify-between">
          {['1. LOCATION', '2. DETAILS', '3. REVIEW'].map((s, i) => (
            <div key={i} className="flex items-center">
              <div className={`w-4 h-4 ${i + 1 < step ? 'bg-text-primary' : i + 1 === step ? 'bg-text-primary w-6 h-6 flex items-center justify-center text-white text-xs font-bold' : 'border-2 border-text-primary'}`} />
              {i < 2 && <div className="w-32 h-[3px] bg-text-primary mx-2" />}
              <span className={`text-xs uppercase ml-2 ${i + 1 === step ? 'font-bold' : 'text-text-muted'}`}>{s.split('. ')[1]}</span>
            </div>
          ))}
        </div>
      </div>

      {step === 1 && (
        <div className="grid grid-cols-2 gap-12">
          <div>
            <label className="label-text block mb-2">WARD *</label>
            <select value={wardId} onChange={e => setWardId(e.target.value)}
              className="w-full h-12 px-4 border-2 border-border-medium bg-surface-elevated text-sm focus:border-text-primary outline-none mb-8">
              <option value="">Select ward</option>
              {KANPUR_WARDS.map(w => <option key={w.id} value={w.id}>{w.name}</option>)}
            </select>

            <label className="label-text block mb-2">SELECT LOCATION ON MAP *</label>
            <div className="h-[400px] border border-border-light mb-8">
              <MapPicker lat={lat} lng={lng} onSelect={handleLocationSelect} />
            </div>

            <label className="label-text block mb-2">COORDINATES</label>
            <div className="border border-border-light p-4 bg-surface-elevated">
              <p className="mono-text">LAT: {lat.toFixed(6)}    LNG: {lng.toFixed(6)}</p>
            </div>
          </div>
          <div className="flex items-end">
            <Button onClick={() => setStep(2)} className="w-full">CONTINUE TO DETAILS →</Button>
          </div>
        </div>
      )}

      {step === 2 && (
        <div className="grid grid-cols-2 gap-12">
          <div />
          <div>
            <label className="label-text block mb-2">CATEGORY *</label>
            <div className="flex gap-4 mb-8">
              {['ROADS', 'WATER', 'GARBAGE'].map(c => (
                <button key={c} onClick={() => setCategory(c)}
                  className={`flex-1 py-6 border-2 text-sm font-bold uppercase ${category === c ? 'text-white' : ''}`}
                  style={{ borderColor: c === 'ROADS' ? '#C24B2A' : c === 'WATER' ? '#0D6B6E' : '#6B7A2A', backgroundColor: category === c ? (c === 'ROADS' ? '#C24B2A' : c === 'WATER' ? '#0D6B6E' : '#6B7A2A') : 'transparent', color: category === c ? 'white' : (c === 'ROADS' ? '#C24B2A' : c === 'WATER' ? '#0D6B6E' : '#6B7A2A') }}>
                  {c}
                </button>
              ))}
            </div>

            <label className="label-text block mb-2">SEVERITY *</label>
            <div className="flex gap-2 mb-8">
              {['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'].map(s => (
                <button key={s} onClick={() => setSeverity(s)}
                  className={`px-4 py-2 border text-xs font-semibold uppercase ${severity === s ? 'border-2 border-text-primary font-bold' : 'border-border-medium text-text-muted'}`}>
                  {s}
                </button>
              ))}
            </div>

            <label className="label-text block mb-2">ISSUE TITLE *</label>
            <input value={title} onChange={e => setTitle(e.target.value)} placeholder="Brief title for the issue"
              className="w-full h-12 px-4 border-2 border-border-medium bg-surface-elevated text-sm focus:border-text-primary outline-none mb-6" />

            <label className="label-text block mb-2">DESCRIPTION *</label>
            <textarea value={description} onChange={e => setDescription(e.target.value)} placeholder="Provide details about the issue..."
              className="w-full h-32 px-4 py-3 border-2 border-border-medium bg-surface-elevated text-sm focus:border-text-primary outline-none resize-y mb-6" />

            <label className="label-text block mb-2">PHOTOS (OPTIONAL)</label>
            <div className="border-2 border-dashed border-border-medium p-8 text-center mb-8">
              <p className="text-sm text-text-secondary">DRAG PHOTOS HERE OR CLICK TO UPLOAD</p>
            </div>

            <div className="flex gap-4">
              <Button variant="outline" onClick={() => setStep(1)} className="flex-1">← BACK</Button>
              <Button onClick={() => setStep(3)} className="flex-1">REVIEW →</Button>
            </div>
          </div>
        </div>
      )}

      {step === 3 && (
        <div className="max-w-[600px] mx-auto">
          <h2 className="text-2xl font-bold mb-6">REVIEW YOUR REPORT</h2>
          <div className="border border-border-light p-6 bg-surface-elevated mb-8">
            <p className="mb-2"><span className="label-text">WARD:</span> {KANPUR_WARDS.find(w => w.id === wardId)?.name}</p>
            <p className="mb-2"><span className="label-text">CATEGORY:</span> {category}</p>
            <p className="mb-2"><span className="label-text">SEVERITY:</span> {severity}</p>
            <p className="mb-2"><span className="label-text">LOCATION:</span> {lat.toFixed(6)}, {lng.toFixed(6)}</p>
            <p className="mb-2"><span className="label-text">TITLE:</span> {title}</p>
            <p className="mb-2"><span className="label-text">DESCRIPTION:</span> {description}</p>
          </div>
          <div className="flex gap-4">
            <Button variant="outline" onClick={() => setStep(2)} className="flex-1">SAVE DRAFT</Button>
            <Button onClick={handleSubmit} disabled={submitting} className="flex-1">
              {submitting ? "SUBMITTING..." : "SUBMIT ISSUE"}
            </Button>
          </div>
        </div>
      )}
    </LayoutShell>
  );
}
