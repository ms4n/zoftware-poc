# Dashboard Components

This folder contains reusable components for the Product Dashboard with floating bottom navigation.

## Components

### `ProductCard`

A reusable card component that displays individual product information including:

- Product logo, name, and category
- Description with truncation
- Status badges (category, status)
- Website link icon button next to product name
- Action buttons (Approve, Reject)

### `ProductCount`

A minimal count display component that shows:

- Large, bold number count
- Descriptive label (e.g., "Approved Products", "Pending Products")
- Centered above the product grid
- Clean, aesthetic design

### `FloatingBottomNav`

A floating bottom navigation bar with tabs:

- **Approved**: Shows approved products
- **Pending**: Shows pending products
- Floating design with rounded corners and shadows
- Smooth transitions and hover effects

### `PendingProducts`

Component for displaying pending products:

- Fetches from `/products/pending` endpoint
- Shows loading, error, and empty states
- Product count display above grid
- Responsive grid layout
- Bottom padding for floating navigation

### `ApprovedProducts`

Component for displaying approved products:

- Fetches from `/products/approved` endpoint
- Shows loading, error, and empty states
- Product count display above grid
- Responsive grid layout
- Bottom padding for floating navigation

### `ProductGrid`

Responsive grid layout for displaying product cards:

- 1 column on mobile
- 2 columns on medium screens
- 3 columns on large screens

### `LoadingState`

Loading spinner with message while fetching data.

### `ErrorState`

Error display with retry button when API calls fail.

### `EmptyState`

Message shown when there are no products:

- **Approved**: Shows checkmark icon and "No Approved Products" message
- **Pending**: Shows clipboard icon and "No Pending Products" message

## App Structure

The main App component now uses:

- **Root (`/`)**: Shows approved products by default
- **Tab Navigation**: Floating bottom bar to switch between approved/pending
- **No Header**: Clean, minimal design without top navigation
- **Product Counts**: Minimal count display above each product grid
- **Responsive Layout**: Proper spacing for floating navigation

## Usage

```tsx
import {
  ProductCard,
  ProductCount,
  FloatingBottomNav,
  PendingProducts,
  ApprovedProducts,
  type Product
} from "./components/dashboard";

// Use in your app
<FloatingBottomNav activeTab="approved" onTabChange={setActiveTab} />
<ProductCount count={5} type="approved" />
<PendingProducts />
<ApprovedProducts />
```

## Props

### ProductCard

- `product: Product` - Product data object

### ProductCount

- `count: number` - Number of products to display
- `type: "approved" | "pending"` - Type of products for labeling

### FloatingBottomNav

- `activeTab: "approved" | "pending"` - Currently active tab
- `onTabChange: (tab: "approved" | "pending") => void` - Tab change handler

### EmptyState

- `type: "approved" | "pending"` - Type of empty state to display

## Types

### Product Interface

```tsx
interface Product {
  id: number;
  name: string;
  description: string;
  website: string;
  logo: string;
  category: string;
  status: string;
}
```

## Styling

All components use Tailwind CSS classes and are fully responsive. The floating navigation uses:

- Fixed positioning at bottom
- Rounded corners and shadows
- Smooth transitions
- Proper z-index for layering

The ProductCount component features:

- Large, bold typography for the number
- Subtle gray text for the label
- Centered alignment above the product grid
- Minimal spacing and clean aesthetics
