import { useCallback, useEffect, useRef, useState } from 'react';

interface SpeechRecognitionAlternativeLike { transcript: string; }
interface SpeechRecognitionResultLike {
  readonly length: number;
  [index: number]: SpeechRecognitionAlternativeLike;
}
interface SpeechRecognitionEventLike extends Event {
  readonly results: ArrayLike<SpeechRecognitionResultLike>;
}
interface SpeechRecognitionErrorEventLike extends Event { readonly error: string; }
interface SpeechRecognitionLike extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  onstart: (() => void) | null;
  onend: (() => void) | null;
  onresult: ((event: SpeechRecognitionEventLike) => void) | null;
  onerror: ((event: SpeechRecognitionErrorEventLike) => void) | null;
  start(): void;
  stop(): void;
  abort(): void;
}
type SpeechRecognitionConstructor = new () => SpeechRecognitionLike;
type SpeechWindow = Window & {
  SpeechRecognition?: SpeechRecognitionConstructor;
  webkitSpeechRecognition?: SpeechRecognitionConstructor;
};

interface UseSpeechToTextOptions {
  value: string;
  onChange: (value: string) => void;
  onSubmit: (value: string) => void;
  language?: string;
  silenceTimeout?: number;
}

function normalizeSpokenPunctuation(value: string) {
  return value
    .replace(/\b(?:dấu\s+)?phẩy\b[.!]?/giu, ',')
    .replace(/\b(?:dấu\s+)?chấm\s+hỏi\b/giu, '?')
    .replace(/\b(?:dấu\s+)?chấm\s+than\b/giu, '!')
    .replace(/\b(?:dấu\s+)?chấm\b/giu, '.')
    .replace(/\b xuống dòng\b/giu, '\n')
    .replace(/[ \t]+([,.!?])/g, '$1')
    .replace(/([,.!?])(?=\S)/g, '$1 ')
    .replace(/[ \t]{2,}/g, ' ')
    .trim();
}

function prepareForSubmit(value: string) {
  return normalizeSpokenPunctuation(value).replace(/[,;:\s]+$/u, '').trim();
}

function getErrorMessage(error: string) {
  if (error === 'not-allowed' || error === 'service-not-allowed') return 'Vui lòng cho phép trình duyệt sử dụng micro.';
  if (error === 'audio-capture') return 'Không tìm thấy micro trên thiết bị.';
  if (error === 'no-speech') return 'Không nhận được giọng nói. Vui lòng thử lại.';
  if (error === 'network') return 'Không thể nhận dạng giọng nói do lỗi kết nối.';
  return 'Không thể nhận dạng giọng nói. Vui lòng thử lại.';
}

export function useSpeechToText({
  value,
  onChange,
  onSubmit,
  language = 'vi-VN',
  silenceTimeout = 2400,
}: UseSpeechToTextOptions) {
  const recognitionRef = useRef<SpeechRecognitionLike | null>(null);
  const silenceTimerRef = useRef<number | null>(null);
  const valueRef = useRef(value);
  const onChangeRef = useRef(onChange);
  const onSubmitRef = useRef(onSubmit);
  const baseTextRef = useRef('');
  const latestValueRef = useRef('');
  const hasSpeechRef = useRef(false);
  const submitOnEndRef = useRef(false);
  const [listening, setListening] = useState(false);
  const [error, setError] = useState('');
  const supported = typeof window !== 'undefined'
    && Boolean((window as SpeechWindow).SpeechRecognition || (window as SpeechWindow).webkitSpeechRecognition);

  useEffect(() => { valueRef.current = value; }, [value]);
  useEffect(() => { onChangeRef.current = onChange; }, [onChange]);
  useEffect(() => { onSubmitRef.current = onSubmit; }, [onSubmit]);

  const clearSilenceTimer = useCallback(() => {
    if (silenceTimerRef.current !== null) window.clearTimeout(silenceTimerRef.current);
    silenceTimerRef.current = null;
  }, []);

  const stopListening = useCallback((submit = false) => {
    clearSilenceTimer();
    submitOnEndRef.current = submit;
    recognitionRef.current?.stop();
  }, [clearSilenceTimer]);

  const toggleListening = useCallback(() => {
    if (recognitionRef.current) {
      stopListening(true);
      return;
    }

    const speechWindow = window as SpeechWindow;
    const Recognition = speechWindow.SpeechRecognition || speechWindow.webkitSpeechRecognition;
    if (!Recognition) {
      setError('Trình duyệt này chưa hỗ trợ nhập bằng giọng nói.');
      return;
    }

    const recognition = new Recognition();
    recognitionRef.current = recognition;
    baseTextRef.current = valueRef.current.trim();
    latestValueRef.current = baseTextRef.current;
    hasSpeechRef.current = false;
    submitOnEndRef.current = true;
    recognition.lang = language;
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.onstart = () => { setError(''); setListening(true); };
    recognition.onresult = (event) => {
      let transcript = '';
      for (let index = 0; index < event.results.length; index += 1) {
        transcript += event.results[index][0]?.transcript ?? '';
      }

      const normalizedTranscript = normalizeSpokenPunctuation(transcript);
      const nextValue = [baseTextRef.current, normalizedTranscript].filter(Boolean).join(' ').trim();
      latestValueRef.current = nextValue;
      hasSpeechRef.current = Boolean(normalizedTranscript);
      onChangeRef.current(nextValue);

      clearSilenceTimer();
      silenceTimerRef.current = window.setTimeout(() => stopListening(true), silenceTimeout);
    };
    recognition.onerror = (event) => {
      clearSilenceTimer();
      submitOnEndRef.current = false;
      setError(getErrorMessage(event.error));
      setListening(false);
    };
    recognition.onend = () => {
      clearSilenceTimer();
      const shouldSubmit = submitOnEndRef.current && hasSpeechRef.current;
      const textToSubmit = prepareForSubmit(latestValueRef.current);
      recognitionRef.current = null;
      submitOnEndRef.current = false;
      setListening(false);
      if (shouldSubmit && textToSubmit) {
        onChangeRef.current(textToSubmit);
        onSubmitRef.current(textToSubmit);
      }
    };

    setListening(true);
    try {
      recognition.start();
    } catch {
      recognitionRef.current = null;
      submitOnEndRef.current = false;
      setListening(false);
      setError('Không thể khởi động micro. Vui lòng thử lại.');
    }
  }, [clearSilenceTimer, language, silenceTimeout, stopListening]);

  useEffect(() => () => {
    clearSilenceTimer();
    submitOnEndRef.current = false;
    recognitionRef.current?.abort();
    recognitionRef.current = null;
  }, [clearSilenceTimer]);

  return { error, listening, stopListening, supported, toggleListening };
}
