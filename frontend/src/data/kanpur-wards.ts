export const KANPUR_CENTER = { lat: 26.4499, lng: 80.3319 };

export const KANPUR_WARDS = [
  { id: 'ward-32', name: 'Ward 32 - Shanti Nagar', lat: 26.4673, lng: 80.3319 },
  { id: 'ward-33', name: 'Ward 33 - Civil Lines', lat: 26.4720, lng: 80.3450 },
  { id: 'ward-34', name: 'Ward 34 - Kidwai Nagar', lat: 26.4580, lng: 80.3200 },
  { id: 'ward-35', name: 'Ward 35 - Kanpur Cantt', lat: 26.4400, lng: 80.3100 },
  { id: 'ward-36', name: 'Ward 36 - Govind Nagar', lat: 26.4250, lng: 80.3350 },
];

export function findNearestWard(lat: number, lng: number) {
  let nearest = KANPUR_WARDS[0];
  let minDist = Infinity;
  for (const ward of KANPUR_WARDS) {
    const dist = Math.sqrt(Math.pow(ward.lat - lat, 2) + Math.pow(ward.lng - lng, 2));
    if (dist < minDist) { minDist = dist; nearest = ward; }
  }
  return nearest;
}