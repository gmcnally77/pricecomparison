'use client';
import { useEffect, useState } from 'react';
import { supabase } from '../utils/supabase';
import { TrendingUp, TrendingDown, Activity, DollarSign, ArrowRight, Zap, Clock } from 'lucide-react';

interface Mover {
  selection_key: string;
  runner_name: string;
  event_name: string;
  sport: string;
  back_now: number;
  lay_now: number;
  back_then: number;
  lay_then: number;
  pct_move: number;
  vol_delta: number;
  spread: number;
  label: 'STEAMER' | 'DRIFTER';
  status: string;
}

interface Props {
  activeSport: string;
}

export default function SteamersPanel({ activeSport }: Props) {
  const [movers, setMovers] = useState<Mover[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchMovers = async () => {
    try {
      const { data, error } = await supabase.rpc('get_steamers', { 
          time_window_minutes: 15 
      });
      if (data) setMovers(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMovers();
    const interval = setInterval(fetchMovers, 10000); 
    return () => clearInterval(interval);
  }, []);

  // 1. FILTER BY SPORT (Fixes Bug #1)
  // Logic: Show if Active is "All" (if you have that tab) OR if matches current sport
  const filteredMovers = movers.filter(m => {
      // Normalize comparison (optional safety)
      if (!activeSport || activeSport === 'All') return true;
      
      // Handle "NFL" vs "American Football" naming mismatches if they exist in your DB
      // For now, strict match based on your existing schema
      return m.sport === activeSport;
  });

  if (loading || filteredMovers.length === 0) return null;

  return (
    <div className="mb-8 space-y-3">
        {/* Section Header */}
        <div className="flex items-center justify-between px-1">
            <h3 className="text-white font-bold text-sm flex items-center gap-2">
                <Zap className="text-yellow-400 fill-yellow-400" size={16} /> 
                SMART MONEY 
                <span className="text-slate-500 font-normal text-xs ml-1">({activeSport} • 15m Window)</span>
            </h3>
        </div>
        
        {/* Grid Layout */}
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {filteredMovers.slice(0, 6).map((m) => {
                const isSteamer = m.label === 'STEAMER';
                const trendColor = isSteamer ? 'text-blue-400' : 'text-pink-400';
                const borderColor = isSteamer ? 'border-blue-500/20' : 'border-pink-500/20';
                
                // Safe Number Formatting
                const fmtPrice = (p: number) => (p ? p.toFixed(2) : '-');
                const pctDisplay = Math.abs(m.pct_move * 100).toFixed(1);
                
                // Direction Logic
                const oldPrice = isSteamer ? m.back_then : m.lay_then;
                const newPrice = isSteamer ? m.back_now : m.lay_now;

                return (
                    <div key={m.selection_key} className={`bg-[#131b2c] border ${borderColor} rounded-lg p-3 shadow-lg relative group`}>
                        
                        {/* ROW 1: HEADER & CONTEXT */}
                        <div className="flex justify-between items-start mb-3 border-b border-slate-800/50 pb-2">
                            <div className="flex flex-col">
                                <div className="flex items-center gap-2">
                                    <span className={`text-[10px] font-bold px-1.5 rounded-sm ${isSteamer ? 'bg-blue-500/20 text-blue-300' : 'bg-pink-500/20 text-pink-300'}`}>
                                        {m.label}
                                    </span>
                                    <span className="text-slate-200 font-bold text-sm truncate max-w-[180px]">
                                        {m.runner_name}
                                    </span>
                                </div>
                                <span className="text-[11px] text-slate-500 mt-0.5 truncate max-w-[220px]">
                                    {m.event_name}
                                </span>
                            </div>
                            <div className="text-right">
                                <span className="text-[10px] text-slate-600 uppercase font-mono block">{m.sport}</span>
                                <span className="text-[10px] text-slate-500 flex items-center justify-end gap-1 mt-0.5">
                                    <Clock size={10} /> 15m
                                </span>
                            </div>
                        </div>

                        {/* ROW 2: PRICE ACTION (THE TRADE) */}
                        <div className="flex items-center justify-between mb-3 px-1">
                            <div className="flex flex-col">
                                <span className="text-[10px] text-slate-500 uppercase font-medium">Price Taken</span>
                                <div className="flex items-center gap-2 text-sm">
                                    <span className="text-slate-500 line-through decoration-slate-600">{fmtPrice(oldPrice)}</span>
                                    <ArrowRight size={12} className="text-slate-600" />
                                    <span className={`font-mono font-bold text-lg ${trendColor}`}>{fmtPrice(newPrice)}</span>
                                    <span className={`text-xs font-medium ml-1 ${trendColor}`}>({pctDisplay}%)</span>
                                </div>
                            </div>
                            
                            <div className="text-right flex flex-col items-end">
                                <span className="text-[10px] text-slate-500 uppercase font-medium">Matched</span>
                                <span className="font-mono text-white text-sm flex items-center gap-0.5">
                                    <span className="text-slate-600">+£</span>
                                    {(m.vol_delta / 1000).toFixed(1)}k
                                </span>
                            </div>
                        </div>

                        {/* ROW 3: EXECUTION (CURRENT STATE) */}
                        <div className="bg-[#0B1120] rounded p-2 flex items-center justify-between text-xs">
                            <div className="flex items-center gap-3">
                                <div className="flex flex-col items-center min-w-[40px]">
                                    <span className="text-[9px] text-blue-500 uppercase mb-0.5">Back</span>
                                    <span className="font-mono font-bold text-white">{fmtPrice(m.back_now)}</span>
                                </div>
                                <div className="w-px h-6 bg-slate-800"></div>
                                <div className="flex flex-col items-center min-w-[40px]">
                                    <span className="text-[9px] text-pink-500 uppercase mb-0.5">Lay</span>
                                    <span className="font-mono font-bold text-white">{fmtPrice(m.lay_now)}</span>
                                </div>
                            </div>
                            
                            <div className="flex flex-col items-end">
                                <span className={`text-[10px] font-medium flex items-center gap-1.5 ${m.spread < 0.05 ? 'text-green-500' : 'text-yellow-600'}`}>
                                    {m.spread < 0.05 ? '● Tight Spread' : '○ Wide Spread'}
                                </span>
                                <span className="text-[9px] text-slate-600 italic mt-0.5">{m.status}</span>
                            </div>
                        </div>

                    </div>
                );
            })}
        </div>
    </div>
  );
}