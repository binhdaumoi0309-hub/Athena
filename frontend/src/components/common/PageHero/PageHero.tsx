import { Link } from 'react-router-dom';
import styles from './PageHero.module.css';

interface PageHeroProps {
  eyebrow?: string;
  title: string;
  description?: string;
  simple?: boolean;
}

export function PageHero({
  eyebrow,
  title,
  description,
  simple = false,
}: PageHeroProps) {
  return (
    <section className={`${styles.hero} ${simple ? styles.simple : ''}`}>
      <div className="container">
        {!simple && (
          <nav aria-label="Breadcrumb">
            <Link to="/">Trang chủ</Link>
            <span>/</span>
            <span aria-current="page">{title}</span>
          </nav>
        )}
        {!simple && eyebrow && <p className={styles.eyebrow}>{eyebrow}</p>}
        <h1>{title}</h1>
        {description && <p className={styles.description}>{description}</p>}
      </div>
    </section>
  );
}
