"""Driver database management with JSON storage."""

import json
from pathlib import Path
from typing import Dict, List, Optional
import logging

from viberesp.core.models import ThieleSmallParameters

logger = logging.getLogger(__name__)


class DriverDatabase:
    """
    Manage driver library with JSON-based storage.

    Provides save/load functionality for driver T/S parameters,
    with search and filtering capabilities.
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize driver database.

        Args:
            db_path: Path to JSON database file.
                     Defaults to ~/.viberesp/drivers.json
        """
        if db_path is None:
            # Default: ~/.viberesp/drivers.json
            home = Path.home()
            db_path = home / '.viberesp' / 'drivers.json'

        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.drivers: Dict[str, ThieleSmallParameters] = {}
        self._load()

    def _load(self) -> None:
        """Load drivers from JSON file."""
        if not self.db_path.exists():
            logger.info(f"Driver database not found at {self.db_path}. Creating new database.")
            self.drivers = {}
            return

        try:
            with open(self.db_path, 'r') as f:
                data = json.load(f)

            for name, driver_dict in data.items():
                try:
                    self.drivers[name] = ThieleSmallParameters(**driver_dict)
                except Exception as e:
                    logger.warning(f"Failed to load driver '{name}': {e}")

            logger.info(f"Loaded {len(self.drivers)} drivers from {self.db_path}")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON database: {e}")
            self.drivers = {}
        except Exception as e:
            logger.error(f"Failed to load database: {e}")
            self.drivers = {}

    def _save(self) -> None:
        """Save drivers to JSON file."""
        try:
            data = {
                name: driver.model_dump()
                for name, driver in self.drivers.items()
            }

            with open(self.db_path, 'w') as f:
                json.dump(data, f, indent=2)

            logger.debug(f"Saved {len(self.drivers)} drivers to {self.db_path}")

        except Exception as e:
            logger.error(f"Failed to save database: {e}")
            raise

    def add_driver(self, name: str, driver: ThieleSmallParameters) -> None:
        """
        Add or update a driver in the database.

        Args:
            name: Unique identifier for the driver
            driver: ThieleSmallParameters instance
        """
        self.drivers[name] = driver
        self._save()
        logger.info(f"Added driver '{name}' to database")

    def get_driver(self, name: str) -> Optional[ThieleSmallParameters]:
        """
        Retrieve a driver by name.

        Args:
            name: Driver identifier

        Returns:
            ThieleSmallParameters if found, None otherwise
        """
        return self.drivers.get(name)

    def remove_driver(self, name: str) -> bool:
        """
        Remove a driver from the database.

        Args:
            name: Driver identifier

        Returns:
            True if removed, False if not found
        """
        if name in self.drivers:
            del self.drivers[name]
            self._save()
            logger.info(f"Removed driver '{name}' from database")
            return True
        return False

    def list_drivers(self) -> List[str]:
        """
        List all driver names in the database.

        Returns:
            List of driver identifiers
        """
        return list(self.drivers.keys())

    def search_drivers(
        self,
        manufacturer: Optional[str] = None,
        min_fs: Optional[float] = None,
        max_fs: Optional[float] = None,
        min_qts: Optional[float] = None,
        max_qts: Optional[float] = None,
        min_vas: Optional[float] = None,
        max_vas: Optional[float] = None,
        enclosure_type: Optional[str] = None
    ) -> Dict[str, ThieleSmallParameters]:
        """
        Search drivers by criteria.

        Args:
            manufacturer: Filter by manufacturer name
            min_fs: Minimum resonance frequency (Hz)
            max_fs: Maximum resonance frequency (Hz)
            min_qts: Minimum total Q
            max_qts: Maximum total Q
            min_vas: Minimum compliance volume (L)
            max_vas: Maximum compliance volume (L)
            enclosure_type: Filter by recommended enclosure type
                             ("sealed", "ported", or None for all)

        Returns:
            Dict of matching drivers
        """
        results = {}

        for name, driver in self.drivers.items():
            # Filter by manufacturer
            if manufacturer and driver.manufacturer != manufacturer:
                continue

            # Filter by Fs range
            if min_fs and driver.fs < min_fs:
                continue
            if max_fs and driver.fs > max_fs:
                continue

            # Filter by Qts range
            qts = driver.qts
            if min_qts and qts < min_qts:
                continue
            if max_qts and qts > max_qts:
                continue

            # Filter by Vas range
            if min_vas and driver.vas < min_vas:
                continue
            if max_vas and driver.vas > max_vas:
                continue

            # Filter by enclosure type recommendation
            if enclosure_type:
                recommended = driver.get_recommended_enclosure()
                if enclosure_type not in recommended:
                    continue

            results[name] = driver

        return results

    def export_drivers(
        self,
        output_path: str,
        driver_names: Optional[List[str]] = None
    ) -> None:
        """
        Export drivers to a JSON file.

        Args:
            output_path: Path for output file
            driver_names: List of drivers to export (all if None)
        """
        if driver_names is None:
            drivers_to_export = self.drivers
        else:
            drivers_to_export = {
                name: self.drivers[name]
                for name in driver_names
                if name in self.drivers
            }

        data = {
            name: driver.model_dump_with_derived()
            for name, driver in drivers_to_export.items()
        }

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"Exported {len(drivers_to_export)} drivers to {output_path}")

    def import_drivers(
        self,
        input_path: str,
        overwrite: bool = False
    ) -> int:
        """
        Import drivers from a JSON file.

        Args:
            input_path: Path to JSON file
            overwrite: Whether to overwrite existing drivers

        Returns:
            Number of drivers imported
        """
        input_path = Path(input_path)

        with open(input_path, 'r') as f:
            data = json.load(f)

        count = 0
        for name, driver_dict in data.items():
            if name in self.drivers and not overwrite:
                logger.warning(f"Driver '{name}' already exists. Skipping.")
                continue

            try:
                self.drivers[name] = ThieleSmallParameters(**driver_dict)
                count += 1
            except Exception as e:
                logger.error(f"Failed to import driver '{name}': {e}")

        self._save()
        logger.info(f"Imported {count} drivers from {input_path}")

        return count

    def get_statistics(self) -> Dict:
        """
        Get statistics about the driver database.

        Returns:
            Dict with database statistics
        """
        if not self.drivers:
            return {
                'total_drivers': 0,
                'manufacturers': {},
                'enclosure_recommendations': {}
            }

        # Count by manufacturer
        manufacturers = {}
        for driver in self.drivers.values():
            if driver.manufacturer:
                manufacturers[driver.manufacturer] = \
                    manufacturers.get(driver.manufacturer, 0) + 1

        # Count by enclosure recommendation
        recommendations = {'sealed': 0, 'ported': 0, 'sealed or ported': 0}
        for driver in self.drivers.values():
            rec = driver.get_recommended_enclosure()
            recommendations[rec] = recommendations.get(rec, 0) + 1

        # Fs, Qts, Vas ranges
        fs_values = [d.fs for d in self.drivers.values()]
        qts_values = [d.qts for d in self.drivers.values()]
        vas_values = [d.vas for d in self.drivers.values()]

        return {
            'total_drivers': len(self.drivers),
            'manufacturers': manufacturers,
            'enclosure_recommendations': recommendations,
            'fs_range': (min(fs_values), max(fs_values)),
            'qts_range': (min(qts_values), max(qts_values)),
            'vas_range': (min(vas_values), max(vas_values)),
        }
