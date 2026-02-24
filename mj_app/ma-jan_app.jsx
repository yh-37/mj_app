import React, { useState, useEffect } from 'react';

const MahjongScoreApp = () => {
    const [members, setMembers] = useState(() => {
        const saved = localStorage.getItem('mahjong-members-v5');
        return saved ? JSON.parse(saved) : ['P1', 'P2', 'P3', 'P4', 'P5', 'P6'];
    });

    const [activePlayers, setActivePlayers] = useState([]);
    const [gameMode, setGameMode] = useState(4);
    const [uma, setUma] = useState({ 1: 30, 2: 10, 3: -10, 4: -30 });
    const [currentPoints, setCurrentPoints] = useState({});
    const [history, setHistory] = useState(() => {
        const saved = localStorage.getItem('mahjong-history-v5');
        return saved ? JSON.parse(saved) : [];
    });
    const [error, setError] = useState('');
    const [editingIndex, setEditingIndex] = useState(null);

    useEffect(() => {
        localStorage.setItem('mahjong-members-v5', JSON.stringify(members));
        localStorage.setItem('mahjong-history-v5', JSON.stringify(history));
    }, [members, history]);

    useEffect(() => {
        const currentUma = Object.values(uma).slice(0, gameMode).reduce((a, b) => a + Number(b), 0);
        if (currentUma !== 0) {
            setError(`ウマ合計: ${currentUma} (不整合)`);
        } else {
            setError('');
        }
    }, [uma, gameMode]);

    useEffect(() => {
        if (editingIndex === null) {
            setActivePlayers(members.slice(0, gameMode));
        }
    }, [gameMode, members, editingIndex]);

    const handleNameChange = (index, newName) => {
        const newMembers = [...members];
        newMembers[index] = newName;
        setMembers(newMembers);
    };

    const togglePlayerActive = (name) => {
        if (editingIndex !== null) return;
        if (activePlayers.includes(name)) {
            setActivePlayers(activePlayers.filter(p => p !== name));
        } else if (activePlayers.length < gameMode) {
            setActivePlayers([...activePlayers, name]);
        } else {
            const [first, ...rest] = activePlayers;
            setActivePlayers([...rest, name]);
        }
    };

    const startEdit = (index) => {
        const round = history[index];
        const editingActive = round.filter(p => p.rawPoint !== undefined).map(p => p.name);
        const editingPoints = {};
        round.forEach(p => {
            if (p.rawPoint !== undefined) editingPoints[p.name] = p.rawPoint;
        });

        setEditingIndex(index);
        setActivePlayers(editingActive);
        setCurrentPoints(editingPoints);
        setGameMode(editingActive.length);
        window.scrollTo({ top: 0, behavior: 'smooth' });
    };

    const calculateScore = () => {
        if (activePlayers.length !== gameMode) {
            alert(`${gameMode}人選んでください。`);
            return;
        }

        let participants = activePlayers.map(name => ({
            name,
            rawPoint: parseInt(currentPoints[name] || 0)
        }));

        participants.sort((a, b) => b.rawPoint - a.rawPoint);

        const getBaseScore = (p) => {
            const diff = p - 30000;
            const hundredDigit = Math.abs(p % 1000 / 100);
            let roundedDiff = (hundredDigit <= 5) ? Math.floor(diff / 1000) * 1000 : Math.ceil(diff / 1000) * 1000;
            return roundedDiff / 1000;
        };

        const rankGroups = [];
        participants.forEach(p => {
            const group = rankGroups.find(g => g[0].rawPoint === p.rawPoint);
            if (group) group.push(p);
            else rankGroups.push([p]);
        });

        let participantResults = [];
        let currentRank = 1;
        rankGroups.forEach(group => {
            const groupSize = group.length;
            let totalUmaForGroup = 0;
            for (let i = 0; i < groupSize; i++) totalUmaForGroup += Number(uma[currentRank + i]);
            const avgUma = totalUmaForGroup / groupSize;
            group.forEach(p => participantResults.push({ ...p, rank: currentRank, base: getBaseScore(p.rawPoint), uma: avgUma }));
            currentRank += groupSize;
        });

        const othersTotal = participantResults.filter(r => r.rank !== 1).reduce((sum, p) => sum + (p.base + p.uma), 0);
        const topCount = participantResults.filter(r => r.rank === 1).length;

        const roundResult = members.map(name => {
            const p = participantResults.find(r => r.name === name);
            if (p) {
                return { name, finalScore: p.rank === 1 ? (othersTotal * -1) / topCount : (p.base + p.uma), rawPoint: p.rawPoint };
            }
            return { name, finalScore: 0 };
        });

        if (editingIndex !== null) {
            const newHistory = [...history];
            newHistory[editingIndex] = roundResult;
            setHistory(newHistory);
            setEditingIndex(null);
        } else {
            setHistory([...history, roundResult]);
        }
        setCurrentPoints({});
    };

    return (
        <div className="p-4 max-w-2xl mx-auto bg-slate-100 min-h-screen pb-10 font-sans text-slate-900">
            <header className="flex justify-between items-center mb-4">
                <h1 className="text-xl font-black tracking-tighter italic text-emerald-800">🀄 MJ-SCORE</h1>
                <button onClick={() => { if (window.confirm('データを全て消去しますか？')) setHistory([]); }} className="text-[10px] text-slate-400 font-bold border border-slate-300 px-2 py-1 rounded hover:bg-white transition">RESET ALL</button>
            </header>

            {/* ウマ入力：一列でコンパクトに */}
            <div className="bg-white px-4 py-2 rounded-2xl shadow-sm border border-slate-200 mb-4 flex items-center justify-between overflow-x-auto whitespace-nowrap">
                <span className="text-[10px] font-black text-slate-400 mr-2 uppercase tracking-tighter">Uma:</span>
                <div className="flex gap-2 items-center">
                    {[...Array(gameMode)].map((_, i) => (
                        <div key={i} className="flex items-center bg-slate-50 rounded-lg px-2 py-1 border border-slate-100">
                            <span className="text-[9px] font-bold text-slate-400 mr-1">{i + 1}位</span>
                            <input
                                type="number"
                                value={uma[i + 1]}
                                onChange={e => setUma({ ...uma, [i + 1]: e.target.value })}
                                className="w-8 bg-transparent border-none p-0 text-center font-bold text-xs focus:ring-0 text-emerald-700"
                            />
                        </div>
                    ))}
                </div>
                {error && <span className="text-red-500 text-[9px] ml-2 font-black animate-pulse">{error}</span>}
            </div>

            {/* スコア入力メインパネル */}
            <div className={`bg-white p-5 rounded-3xl shadow-lg border-t-8 mb-6 transition-all ${editingIndex !== null ? 'border-orange-500 ring-4 ring-orange-50' : 'border-emerald-600'}`}>
                <div className="flex justify-between items-center mb-6">
                    <h2 className="font-black text-slate-400 text-[10px] uppercase tracking-[0.2em]">
                        {editingIndex !== null ? `Editing Round ${editingIndex + 1}` : 'Player Entry'}
                    </h2>
                    {editingIndex === null && (
                        <div className="flex bg-slate-100 rounded-xl p-1">
                            {[3, 4].map(num => (
                                <button key={num} onClick={() => setGameMode(num)} className={`px-4 py-1 rounded-lg text-xs font-black transition ${gameMode === num ? 'bg-white shadow text-emerald-700' : 'text-slate-400'}`}>{num}麻</button>
                            ))}
                        </div>
                    )}
                </div>

                <div className="space-y-3 mb-6">
                    {members.map((name, i) => {
                        const isActive = activePlayers.includes(name);
                        return (
                            <div key={i} className={`flex gap-3 items-center p-2 rounded-2xl transition-all ${isActive ? 'bg-emerald-50 border border-emerald-100' : 'bg-slate-50 opacity-40 grayscale scale-95'}`}>
                                <button
                                    onClick={() => togglePlayerActive(name)}
                                    className={`w-10 h-10 rounded-xl flex items-center justify-center text-sm font-black transition ${isActive ? 'bg-emerald-600 text-white shadow-md' : 'bg-slate-200 text-slate-400'}`}
                                >
                                    {isActive ? '✔' : '+'}
                                </button>
                                <input
                                    type="text"
                                    value={name}
                                    onChange={(e) => handleNameChange(i, e.target.value)}
                                    className="w-20 bg-transparent text-sm font-bold border-none p-0 focus:ring-0"
                                />
                                <input
                                    type="number"
                                    step="100"
                                    placeholder="0"
                                    disabled={!isActive}
                                    value={currentPoints[name] || ''}
                                    onChange={e => setCurrentPoints({ ...currentPoints, [name]: e.target.value })}
                                    className="flex-1 bg-transparent border-b border-slate-200 text-right font-mono text-lg outline-none focus:border-emerald-500"
                                />
                            </div>
                        );
                    })}
                </div>

                <div className="flex gap-3">
                    {editingIndex !== null && (
                        <button onClick={() => { setEditingIndex(null); setCurrentPoints({}); }} className="flex-1 bg-slate-200 text-slate-600 py-4 rounded-2xl font-black text-xs">CANCEL</button>
                    )}
                    <button
                        onClick={calculateScore}
                        disabled={!!error || activePlayers.length !== gameMode}
                        className={`flex-[2] py-4 rounded-2xl font-black text-xs shadow-xl transition active:scale-95 ${editingIndex !== null ? 'bg-orange-500 text-white' : 'bg-emerald-600 text-white disabled:bg-slate-300'}`}
                    >
                        {editingIndex !== null ? 'UPDATE RECORD' : `CONFIRM ${gameMode} PLAYERS`}
                    </button>
                </div>
            </div>

            {/* 履歴とトータル */}
            {history.length > 0 && (
                <div className="bg-slate-900 rounded-3xl shadow-xl overflow-hidden border border-slate-800">
                    <div className="p-4 bg-slate-800/50 flex justify-between items-center border-b border-slate-800">
                        <h3 className="text-white font-black text-[10px] tracking-widest uppercase">Summary</h3>
                        <span className="text-[10px] text-emerald-400 font-mono italic">Total {history.length} games</span>
                    </div>
                    <div className="overflow-x-auto">
                        <table className="w-full text-xs">
                            <thead>
                                <tr className="text-slate-500 font-bold border-b border-slate-800">
                                    <th className="px-4 py-3 text-left">Player</th>
                                    {history.map((_, idx) => (
                                        <th key={idx} onClick={() => startEdit(idx)} className="px-2 py-3 text-right text-emerald-500 hover:text-emerald-300 cursor-pointer transition">#{idx + 1}</th>
                                    ))}
                                    <th className="px-4 py-3 text-right text-white bg-slate-800">TOTAL</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-800">
                                {members.map(name => {
                                    const total = history.reduce((sum, round) => sum + (round.find(r => r.name === name)?.finalScore || 0), 0);
                                    return (
                                        <tr key={name}>
                                            <td className="px-4 py-3 font-bold text-slate-300 bg-slate-800/20">{name}</td>
                                            {history.map((round, idx) => {
                                                const score = round.find(r => r.name === name)?.finalScore || 0;
                                                return (
                                                    <td key={idx} className={`px-2 py-3 text-right font-mono ${score > 0 ? 'text-orange-400' : score < 0 ? 'text-blue-400' : 'text-slate-600'}`}>
                                                        {score === 0 ? '0' : score > 0 ? `+${score.toFixed(1)}` : score.toFixed(1)}
                                                    </td>
                                                );
                                            })}
                                            <td className={`px-4 py-3 text-right font-mono font-black text-sm bg-slate-800/40 ${total >= 0 ? 'text-orange-500' : 'text-blue-500'}`}>
                                                {total > 0 ? `+${total.toFixed(1)}` : total.toFixed(1)}
                                            </td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}
        </div>
    );
};

export default MahjongScoreApp;