#include <bananas_aruco/affine_rotation.h>

#include <array>
#include <utility>

#include <Eigen/Core>
#include <Eigen/Geometry>

#include <nlohmann/json.hpp>

#include <opencv2/core/eigen.hpp>
#include <opencv2/core/matx.hpp>
#include <opencv2/core/types.hpp>

namespace affine_rotation {

AffineRotation::AffineRotation()
    : rotation_{1.0F, 0.0F, 0.0F, 0.0F}, translation_{0.0F, 0.0F, 0.0F} {};
AffineRotation::AffineRotation(Eigen::Quaternionf rotation,
                               Eigen::Vector3f translation)
    // NOTE: The moves don't do anything, but clang-tidy doesn't know this.
    : rotation_{std::move(rotation)}, translation_{std::move(translation)} {};

auto AffineRotation::operator*(const AffineRotation &other) const
    -> AffineRotation {
    return {rotation_ * other.rotation_,
            translation_ + rotation_ * other.translation_};
}

auto AffineRotation::operator*(cv::Point3f point) const -> cv::Point3f {
    const Eigen::Vector3f point_vec{point.x, point.y, point.z};
    const Eigen::Vector3f result{translation_ + rotation_ * point_vec};
    return {result.x(), result.y(), result.z()};
}

auto AffineRotation::inverse() const -> AffineRotation {
    const auto rotation_inverse{rotation_.inverse()};
    return {rotation_inverse, -(rotation_inverse * translation_)};
}

auto AffineRotation::getTranslation() const -> Eigen::Vector3f {
    return translation_;
}

auto AffineRotation::getRotation() const -> Eigen::Quaternionf {
    return rotation_;
}

void from_json(const nlohmann::json &j, AffineRotation &affine_rotation) {
    std::array<float, 4> rotation{};
    j.at("rotation").get_to(rotation);

    std::array<float, 3> translation{};
    j.at("translation").get_to(translation);

    affine_rotation = {{rotation[0], rotation[1], rotation[2], rotation[3]},
                       {translation[0], translation[1], translation[2]}};
}

void to_json(nlohmann::json &j, const AffineRotation &affine_rotation) {
    // TODO(vainiovano): Test that this actually works.
    j["translation"] = affine_rotation.getTranslation();
    const std::array<float, 4> rotation{
        affine_rotation.getRotation().w(),
        affine_rotation.getRotation().x(),
        affine_rotation.getRotation().y(),
        affine_rotation.getRotation().z(),
    };
    j["rotation"] = rotation;
}

auto from_cv(const cv::Vec3f &rvec, const cv::Vec3f &tvec) -> AffineRotation {
    Eigen::Vector3f rotation_vec;
    Eigen::Vector3f translation;
    cv::cv2eigen(rvec, rotation_vec);
    cv::cv2eigen(tvec, translation);

    const float angle{rotation_vec.norm()};
    const Eigen::AngleAxisf rotation{angle, rotation_vec / angle};
    return {Eigen::Quaternionf{rotation}, translation};
}

} // namespace affine_rotation
