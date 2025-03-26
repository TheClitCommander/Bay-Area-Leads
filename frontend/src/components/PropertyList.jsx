import React from 'react';
import { useQuery } from 'react-query';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';

// Components
import PropertyCard from './PropertyCard';
import LoadingCard from './LoadingCard';
import EmptyState from './EmptyState';

// Hooks
import useSearch from '../hooks/useSearch';
import useFilters from '../hooks/useFilters';

function PropertyList() {
  const navigate = useNavigate();
  const { searchQuery } = useSearch();
  const { filters } = useFilters();
  
  // Fetch properties
  const { data, isLoading, error } = useQuery(
    ['properties', searchQuery, filters],
    () => fetch(`/api/search?q=${searchQuery}`).then(res => res.json())
  );
  
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {[...Array(6)].map((_, i) => (
          <LoadingCard key={i} />
        ))}
      </div>
    );
  }
  
  if (error) {
    return (
      <EmptyState
        icon="🚨"
        title="Oops!"
        description="Something went wrong loading the properties."
        action={{
          label: "Try Again",
          onClick: () => window.location.reload()
        }}
      />
    );
  }
  
  if (!data?.results?.length) {
    return (
      <EmptyState
        icon="🏠"
        title="No properties found"
        description="Try adjusting your search or filters"
        action={{
          label: "Clear Filters",
          onClick: () => {/* clear filters */}
        }}
      />
    );
  }
  
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {data.results.map((property, index) => (
        <motion.div
          key={property.id}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, delay: index * 0.1 }}
        >
          <PropertyCard
            property={property}
            onClick={() => navigate(`/property/${property.id}`)}
          />
        </motion.div>
      ))}
    </div>
  );
}

export default PropertyList;
