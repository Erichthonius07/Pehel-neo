"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { authApi } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { Button } from "@/components/ui/button";

export default function LoginPage() {
  const [phone, setPhone] = useState("");
  const [otp, setOtp] = useState("");
  const [otpSent, setOtpSent] = useState(false);
  const [otpCode, setOtpCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showAuthority, setShowAuthority] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  
  const router = useRouter();
  const { loginCitizen, loginAuthority } = useAuth();

  const handleSendOtp = async () => {
    setLoading(true); setError("");
    try {
      const res = await authApi.sendOtp(phone.startsWith("+91") ? phone : `+91${phone}`);
      setOtpCode(res.otp);
      setOtpSent(true);
    } catch (e) { setError("Failed to send OTP"); }
    setLoading(false);
  };

  const handleVerifyOtp = async () => {
    setLoading(true); setError("");
    try {
      const res = await authApi.verifyOtp(phone.startsWith("+91") ? phone : `+91${phone}`, otp);
      loginCitizen(res.access_token);
      router.push("/dashboard");
    } catch (e) { setError("Invalid OTP"); }
    setLoading(false);
  };

  const handleAuthorityLogin = async () => {
    setLoading(true); setError("");
    try {
      const res = await authApi.authorityLogin(email, password);
      loginAuthority(res.access_token);
      router.push("/authority");
    } catch (e) { setError("Invalid credentials"); }
    setLoading(false);
  };

  if (showAuthority) {
    return (
      <div className="flex min-h-screen">
        <div className="w-1/2 flex flex-col justify-center px-16 bg-surface-primary">
          <h1 className="text-6xl font-black tracking-tight text-text-primary mb-8">PEHEL NEO</h1>
          <p className="text-4xl font-extrabold leading-none mb-2">GOVERNANCE</p>
          <p className="text-4xl font-medium leading-none mb-2">MADE OBSERVABLE</p>
          <p className="text-2xl font-light leading-tight mb-8">THROUGH UNDENIABLE EVIDENCE</p>
          <div className="hairline mb-6" />
          <p className="mono-text text-text-secondary">KANPUR PILOT</p>
          <p className="mono-text text-text-secondary">5 WARDS ACTIVE</p>
          <p className="mono-text text-text-secondary">CIVIC ACCOUNTABILITY PLATFORM</p>
        </div>
        <div className="w-1/2 flex flex-col justify-center px-16 bg-surface-pure">
          <p className="label-text mb-6">AUTHORITY LOGIN</p>
          <input type="email" placeholder="Email" value={email} onChange={e => setEmail(e.target.value)}
            className="w-full h-12 px-4 border-2 border-border-medium bg-surface-elevated text-sm focus:border-text-primary outline-none mb-4" />
          <input type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)}
            className="w-full h-12 px-4 border-2 border-border-medium bg-surface-elevated text-sm focus:border-text-primary outline-none mb-6" />
          <Button onClick={handleAuthorityLogin} disabled={loading} className="w-full h-12 mb-6">
            {loading ? "LOGGING IN..." : "LOGIN"}
          </Button>
          {error && <p className="text-priority-high text-xs uppercase mb-4">{error}</p>}
          <div className="hairline mb-6" />
          <button onClick={() => setShowAuthority(false)} className="text-xs uppercase text-text-secondary hover:text-text-primary">
            CITIZEN LOGIN →
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen">
      <div className="w-1/2 flex flex-col justify-center px-16 bg-surface-primary">
        <h1 className="text-6xl font-black tracking-tight text-text-primary mb-8">PEHEL NEO</h1>
        <p className="text-4xl font-extrabold leading-none mb-2">GOVERNANCE</p>
        <p className="text-4xl font-medium leading-none mb-2">MADE OBSERVABLE</p>
        <p className="text-2xl font-light leading-tight mb-8">THROUGH UNDENIABLE EVIDENCE</p>
        <div className="hairline mb-6" />
        <p className="mono-text text-text-secondary">KANPUR PILOT</p>
        <p className="mono-text text-text-secondary">5 WARDS ACTIVE</p>
        <p className="mono-text text-text-secondary">CIVIC ACCOUNTABILITY PLATFORM</p>
      </div>
      <div className="w-1/2 flex flex-col justify-center px-16 bg-surface-pure">
        <p className="label-text mb-6">CITIZEN LOGIN</p>
        <div className="flex mb-4">
          <span className="flex items-center px-4 h-12 border-2 border-r-0 border-border-medium bg-surface-elevated text-sm text-text-muted">+91</span>
          <input type="tel" placeholder="Enter mobile number" value={phone} onChange={e => setPhone(e.target.value)}
            className="flex-1 h-12 px-4 border-2 border-border-medium bg-surface-elevated text-sm focus:border-text-primary outline-none" />
        </div>
        <Button onClick={handleSendOtp} disabled={loading || phone.length < 10} className="w-full h-12 mb-8">
          {loading ? "SENDING..." : "SEND OTP"}
        </Button>
        
        {otpSent && (
          <>
            <p className="label-text mb-4">ENTER OTP</p>
            <div className="flex gap-2 mb-4">
              {[0,1,2,3,4,5].map(i => (
                <input key={i} type="text" maxLength={1} value={otp[i] || ""}
                  onChange={e => {
                    const newOtp = otp.split(''); newOtp[i] = e.target.value;
                    setOtp(newOtp.join(''));
                    if (e.target.value && i < 5) {
                            const nextInput = document.querySelectorAll('input[type="text"]')[i+2] as HTMLInputElement | undefined;
                            nextInput?.focus();
                    }
                  }}
                  className="w-12 h-12 border-2 border-border-medium text-center text-lg font-mono focus:border-text-primary outline-none" />
              ))}
            </div>
            <p className="mono-text text-priority-high text-xs mb-4">OTP: {otpCode} (demo)</p>
            <Button onClick={handleVerifyOtp} disabled={loading || otp.length !== 6} className="w-full h-12 mb-4">
              {loading ? "VERIFYING..." : "VERIFY OTP"}
            </Button>
          </>
        )}
        
        {error && <p className="text-priority-high text-xs uppercase mb-4 animation-stampError">{error}</p>}
        <div className="hairline mb-6" />
        <button onClick={() => setShowAuthority(true)} className="text-xs uppercase text-text-secondary hover:text-text-primary">
          AUTHORITY LOGIN →
        </button>
      </div>
    </div>
  );
}