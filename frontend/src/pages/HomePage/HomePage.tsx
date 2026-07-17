import { HeroSection } from '../../components/home/HeroSection';
import { HomeSections } from '../../components/home/HomeSections';
import styles from './HomePage.module.css';
export function HomePage(){return <div className={styles.page}><HeroSection/><HomeSections/></div>}
