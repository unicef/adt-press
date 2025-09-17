import { useState, useCallback } from 'react';
import { Plate } from '../types/plate';

export const usePlate = () => {
  const [plate, setPlate] = useState<Plate | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadPlate = useCallback(async (file: File) => {
    setLoading(true);
    setError(null);
    
    try {
      const text = await file.text();
      const plateData = JSON.parse(text) as Plate;
      setPlate(plateData);
    } catch (err) {
      setError('Failed to parse plate file: ' + (err as Error).message);
    } finally {
      setLoading(false);
    }
  }, []);

  const savePlate = useCallback(() => {
    if (!plate) return;
    
    const dataStr = JSON.stringify(plate, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    
    const link = document.createElement('a');
    link.href = URL.createObjectURL(dataBlob);
    link.download = `${plate.title}-edited.json`;
    link.click();
  }, [plate]);

  const updatePlate = useCallback((updater: (plate: Plate) => Plate) => {
    setPlate(prev => prev ? updater(prev) : null);
  }, []);

  return {
    plate,
    loading,
    error,
    loadPlate,
    savePlate,
    updatePlate,
    setPlate,
  };
};