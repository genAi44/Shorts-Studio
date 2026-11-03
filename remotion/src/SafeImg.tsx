import React, {useState} from 'react';

/**
 * A drop-in replacement for Remotion's <Img /> that NEVER aborts the render
 * (cancelRenderInternal) on 404 or image decode failure.
 * If an asset fails to load, it gracefully falls back or hides itself.
 */
export const SafeImg: React.FC<
  React.ImgHTMLAttributes<HTMLImageElement> & {fallbackSrc?: string}
> = ({src, fallbackSrc, style, onError, ...rest}) => {
  const [currentSrc, setCurrentSrc] = useState<string | undefined>(src);
  const [failed, setFailed] = useState<boolean>(false);

  return (
    <img
      src={currentSrc}
      style={{
        ...style,
        display: failed && !fallbackSrc ? 'none' : (style?.display ?? 'block'),
      }}
      onError={(e) => {
        if (!failed && fallbackSrc && currentSrc !== fallbackSrc) {
          setFailed(true);
          setCurrentSrc(fallbackSrc);
        } else {
          setFailed(true);
          (e.currentTarget as HTMLElement).style.display = 'none';
        }
        if (onError) onError(e);
      }}
      {...rest}
    />
  );
};

